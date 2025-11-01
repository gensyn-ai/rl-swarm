from types import TracebackType
from typing import Optional, Type

import torch
import torch.distributed as dist
import torch.nn.functional as F

from ._modeling_qwen2_moe import Qwen2MoeForCausalLM, Qwen2MoeSparseMoeBlock
from .moe_generate import moe_generate


class _AllDispatch(torch.autograd.Function):
    @staticmethod
    def forward(ctx, hidden_states, expert_mask, pg):
        ctx.pg = pg
        ctx.orig_shape = hidden_states.shape
        ctx.save_for_backward(expert_mask)
        device = hidden_states.device
        group_rank = dist.get_rank(group=pg)
        group_size = dist.get_world_size(group=pg)

        # Split hidden states to tensors to send to each expert.
        hidden_states_send_buffer = [[] for _ in range(group_size)]

        for expert_idx in range(group_size):
            _, top_x = torch.where(expert_mask[expert_idx])
            hidden_states_send_buffer[expert_idx] = hidden_states[None, top_x].reshape(
                -1, hidden_states.shape[-1]
            )

        ctx.hidden_states_send_buffer_shapes = [
            buffer.shape for buffer in hidden_states_send_buffer
        ]
        tokens_to_send = [
            torch.tensor(buffer.shape[0], device=device, dtype=torch.int64)
            for buffer in hidden_states_send_buffer
        ]
        tokens_to_receive = [
            torch.tensor(0, device=device, dtype=torch.int64) for _ in range(group_size)
        ]
        handles = []
        for irank in range(group_size):
            if group_rank == irank:
                handles.append(
                    dist.scatter(
                        tokens_to_receive[irank],
                        scatter_list=tokens_to_send,
                        src=dist.get_global_rank(pg, irank) if pg else irank,
                        group=pg,
                        async_op=True,
                    )
                )
            else:
                handles.append(
                    dist.scatter(
                        tokens_to_receive[irank],
                        src=dist.get_global_rank(pg, irank) if pg else irank,
                        group=pg,
                        async_op=True,
                    )
                )
        for handle in handles:
            handle.wait()

        # Receive buffer for tokens.
        hidden_states_recv_buffer = [
            torch.zeros(
                (tokens_to_receive[irank], hidden_states.shape[-1]),
                device=device,
                dtype=hidden_states.dtype,
            )
            for irank in range(group_size)
        ]

        # Dispatch all hidden states to all experts.
        handles = []
        for irank in range(group_size):
            if group_rank == irank:
                handles.append(
                    dist.scatter(
                        hidden_states_recv_buffer[irank],
                        scatter_list=hidden_states_send_buffer,
                        src=dist.get_global_rank(pg, irank) if pg else irank,
                        group=pg,
                        async_op=True,
                    )
                )
            else:
                handles.append(
                    dist.scatter(
                        hidden_states_recv_buffer[irank],
                        src=dist.get_global_rank(pg, irank) if pg else irank,
                        group=pg,
                        async_op=True,
                    )
                )
        for handle in handles:
            handle.wait()

        ctx.output_indices = [0]
        for buffer in hidden_states_recv_buffer:
            ctx.output_indices.append(ctx.output_indices[-1] + buffer.shape[0])
        return (
            torch.cat(hidden_states_recv_buffer, dim=0),
            ctx.output_indices,
            ctx.hidden_states_send_buffer_shapes,
        )

    @staticmethod
    def backward(ctx, grad_outputs, *_):
        pg = ctx.pg
        group_rank = dist.get_rank(group=pg)
        group_size = dist.get_world_size(group=pg)
        dtype = grad_outputs.dtype
        device = grad_outputs.device
        hidden_states_send_buffer = [
            torch.zeros(hidden_states_send_buffer_shape, device=device, dtype=dtype)
            for hidden_states_send_buffer_shape in ctx.hidden_states_send_buffer_shapes
        ]
        hidden_state_recv_buffer = []
        for export_idx in range(group_size):
            hidden_state_recv_buffer.append(
                grad_outputs[
                    ctx.output_indices[export_idx] : ctx.output_indices[export_idx + 1],
                    :,
                ]
            )

        # Communicate back the gradients
        handles = []
        for irank in range(group_size):
            if group_rank == irank:
                handles.append(
                    dist.scatter(
                        hidden_states_send_buffer[irank],
                        scatter_list=hidden_state_recv_buffer,
                        src=dist.get_global_rank(pg, irank) if pg else irank,
                        group=pg,
                        async_op=True,
                    )
                )
            else:
                handles.append(
                    dist.scatter(
                        hidden_states_send_buffer[irank],
                        src=dist.get_global_rank(pg, irank) if pg else irank,
                        group=pg,
                        async_op=True,
                    )
                )
        grad_input = torch.zeros(ctx.orig_shape, device=device, dtype=dtype)
        (expert_mask,) = ctx.saved_tensors
        for expert_idx in range(group_size):
            handles[expert_idx].wait()
            _, top_x = torch.where(expert_mask[expert_idx])
            grad_input.index_add_(0, top_x, hidden_states_send_buffer[irank])
        return grad_input, None, None


class _AllCombine(torch.autograd.Function):
    @staticmethod
    def forward(
        ctx,
        hidden_states,
        expert_mask,
        output_indices,
        hidden_states_send_buffer_shapes,
        pg,
    ):
        ctx.pg = pg
        ctx.hidden_states_send_buffer_shapes = hidden_states_send_buffer_shapes
        ctx.output_indices = output_indices
        dtype = hidden_states.dtype
        device = hidden_states.device

        group_rank = dist.get_rank(group=pg)
        group_size = dist.get_world_size(group=pg)

        # Split hidden states to tensors to send to each expert.
        ctx.save_for_backward(expert_mask)
        hidden_states_send_buffer = [
            torch.zeros(hidden_states_send_buffer_shape, device=device, dtype=dtype)
            for hidden_states_send_buffer_shape in ctx.hidden_states_send_buffer_shapes
        ]

        hidden_states_recv_buffer = []
        for export_idx in range(group_size):
            hidden_states_recv_buffer.append(
                hidden_states[
                    ctx.output_indices[export_idx] : ctx.output_indices[export_idx + 1],
                    :,
                ]
            )
        handles = []
        for irank in range(group_size):
            if group_rank == irank:
                handles.append(
                    dist.scatter(
                        hidden_states_send_buffer[irank],
                        scatter_list=hidden_states_recv_buffer,
                        src=dist.get_global_rank(pg, irank) if pg else irank,
                        group=pg,
                        async_op=True,
                    )
                )
            else:
                handles.append(
                    dist.scatter(
                        hidden_states_send_buffer[irank],
                        src=dist.get_global_rank(pg, irank) if pg else irank,
                        group=pg,
                        async_op=True,
                    )
                )
        for handle in handles:
            handle.wait()
        ctx.input_indices = [0]
        for buffer in hidden_states_send_buffer:
            ctx.input_indices.append(ctx.input_indices[-1] + buffer.shape[0])
        return torch.cat(hidden_states_send_buffer, dim=0), ctx.input_indices

    @staticmethod
    def backward(ctx, grad_outputs, *_):
        pg = ctx.pg
        dtype = grad_outputs.dtype
        device = grad_outputs.device
        group_rank = dist.get_rank(group=pg)
        group_size = dist.get_world_size(group=pg)

        hidden_states_send_buffer = []
        hidden_states_recv_buffer = []
        for export_idx in range(group_size):
            hidden_states_send_buffer.append(
                grad_outputs[
                    ctx.input_indices[export_idx] : ctx.input_indices[export_idx + 1], :
                ]
            )
        for export_idx in range(group_size):
            hidden_states_recv_buffer.append(
                torch.zeros(
                    (
                        ctx.output_indices[export_idx + 1]
                        - ctx.output_indices[export_idx],
                        grad_outputs.shape[-1],
                    ),
                    device=device,
                    dtype=dtype,
                )
            )
        handles = []
        for irank in range(group_size):
            if group_rank == irank:
                handles.append(
                    dist.scatter(
                        hidden_states_recv_buffer[irank],
                        scatter_list=hidden_states_send_buffer,
                        src=dist.get_global_rank(pg, irank) if pg else irank,
                        group=pg,
                        async_op=True,
                    )
                )
            else:
                handles.append(
                    dist.scatter(
                        hidden_states_recv_buffer[irank],
                        src=dist.get_global_rank(pg, irank) if pg else irank,
                        group=pg,
                        async_op=True,
                    )
                )
        for handle in handles:
            handle.wait()
        return torch.cat(hidden_states_recv_buffer, dim=0), None, None, None, None


class _DistributedQwen2MoeSparseMoeBlock(torch.nn.Module):
    def __init__(
        self,
        layer: Qwen2MoeSparseMoeBlock,
        top_k: int | None = None,
        pg: dist.ProcessGroup = None,
    ):
        super().__init__()
        self.layer = layer
        self.top_k = top_k or layer.top_k
        self.pg = pg
        self.device = self.layer.gate.weight.device
        self.dtype = self.layer.gate.weight.dtype

        # Assume there is one expert per rank.
        assert layer.num_experts == 1, f"{layer.num_experts=}"

        group_rank = dist.get_rank(group=pg)
        group_size = dist.get_world_size(group=pg)
        hidden_dimension = self.layer.gate.weight.shape[1]
        assert self.layer.gate.weight.shape[0] == 1, f"{self.layer.gate.weight.shape=}"

        expert_gates = [
            torch.zeros((1, hidden_dimension), dtype=self.dtype, device=self.device)
            for _ in range(group_size)
        ]
        expert_gates[group_rank] = self.layer.gate.weight
        handles = [
            dist.broadcast(
                expert_gates[irank],
                src=dist.get_global_rank(pg, irank) if pg else irank,
                group=pg,
                async_op=True,
            )
            for irank in range(group_size)
        ]
        for handle in handles:
            handle.wait()
        weight_ = torch.cat(expert_gates, dim=0)
        self.num_experts = weight_.shape[0]
        self.combined_gate = torch.nn.Linear(
            weight_.shape[1], weight_.shape[0], bias=False
        ).to(self.device)
        self.combined_gate.weight.data = weight_

    def all_dispatch_and_combine(
        self,
        routing_weights: torch.Tensor,
        selected_experts: torch.Tensor,
        hidden_states: torch.Tensor,
    ) -> torch.Tensor:
        final_expert_output = torch.zeros_like(hidden_states)
        expert_mask = torch.nn.functional.one_hot(
            selected_experts, num_classes=self.num_experts
        ).permute(2, 1, 0)

        # dispatch the tokens to the corresponding experts
        (
            hidden_states,
            output_indices,
            hidden_states_send_buffer_shapes,
        ) = _AllDispatch.apply(hidden_states, expert_mask, self.pg)

        # compute local expert's outputs on the received tokens
        outputs = self.layer.experts[0](hidden_states)

        # gather the token outputs from the experts
        expert_outputs, input_indices = _AllCombine.apply(
            outputs,
            expert_mask,
            output_indices,
            hidden_states_send_buffer_shapes,
            self.pg,
        )

        for expert_idx in range(self.num_experts):
            idx, top_x = torch.where(expert_mask[expert_idx])
            expert_output = expert_outputs[
                input_indices[expert_idx] : input_indices[expert_idx + 1], :
            ]

            # Multiple the received expert hidden states by routing weights.
            current_hidden_states = expert_output * routing_weights[top_x, idx, None]
            final_expert_output.index_add_(
                0, top_x, current_hidden_states.to(hidden_states.dtype)
            )
        return final_expert_output

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        batch_size, sequence_length, hidden_dim = hidden_states.shape
        hidden_states = hidden_states.view(-1, hidden_dim)

        # Evaluate the router logits
        router_logits = self.combined_gate(hidden_states)
        routing_weights = F.softmax(router_logits, dim=1, dtype=self.dtype)
        routing_weights, selected_experts = torch.topk(
            routing_weights, self.top_k, dim=-1
        )

        return (
            self.layer.shared_expert(hidden_states)
            + self.all_dispatch_and_combine(
                routing_weights, selected_experts, hidden_states
            )
        ).view(batch_size, sequence_length, hidden_dim)


class DistributedMoEContext:
    def __init__(
        self,
        moe_model: Qwen2MoeForCausalLM,
        top_k: int | None = None,
        pg: dist.ProcessGroup = None,
    ):
        super().__init__()
        self.moe_model = moe_model
        self.orig_generate = None
        self.top_k = top_k
        self.pg = pg

    def __enter__(self):
        # Patch generation function in MoE model with the distributed version.
        self.orig_generate = getattr(self.moe_model, "generate", None)
        self.moe_model.generate = moe_generate(self.moe_model, self.pg)

        # Wrap sparse MoE layers with the distributed MoE layer.
        for layer in self.moe_model.model.layers:
            if isinstance(layer.mlp, Qwen2MoeSparseMoeBlock):
                layer.mlp = _DistributedQwen2MoeSparseMoeBlock(
                    layer.mlp, self.top_k, self.pg
                )

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        # Unwrap the distributed MoE layers and replace with local layers.
        self.moe_model.generate = self.orig_generate

        for layer in self.moe_model.model.layers:
            if isinstance(layer.mlp, _DistributedQwen2MoeSparseMoeBlock):
                # Overwrite the local expert gate with the corresponding tensor from
                # the global router.
                expert_idx = dist.get_rank(group=self.pg)
                expert_weights = layer.mlp.combined_gate.weight.data[
                    expert_idx, :
                ].unsqueeze(dim=0)
                layer.mlp = layer.mlp.layer
                layer.mlp.gate.weight.data = expert_weights
