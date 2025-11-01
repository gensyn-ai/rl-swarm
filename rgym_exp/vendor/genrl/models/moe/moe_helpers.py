from typing import Sequence

import torch
from transformers import Qwen2ForCausalLM, Qwen2MoeConfig

from ._modeling_qwen2_moe import Qwen2MoeForCausalLM, Qwen2MoeSparseMoeBlock


def from_qwen_to_moe(
    qwen_model: Qwen2ForCausalLM,
    num_experts: int,
    num_experts_per_tok: int,
    moe_intermediate_size: int | None = None,
) -> Qwen2MoeForCausalLM:
    config = Qwen2MoeConfig(
        **qwen_model.config.to_dict(),
        num_experts=num_experts,
        num_experts_per_tok=num_experts_per_tok,
        shared_expert_intermediate_size=qwen_model.config.intermediate_size,
        moe_intermediate_size=moe_intermediate_size
        or qwen_model.config.intermediate_size,
    )
    moe_model = Qwen2MoeForCausalLM(config)

    # Copy embeddings & normalization layer.
    moe_model.set_input_embeddings(qwen_model.get_input_embeddings())
    moe_model.set_output_embeddings(qwen_model.get_output_embeddings())
    moe_model.model.norm.weight = qwen_model.model.norm.weight

    # Copy all decoder layer parameters.
    for moe_layer, layer in zip(moe_model.model.layers, qwen_model.model.layers):
        # Layer norms
        moe_layer.input_layernorm.weight = layer.input_layernorm.weight
        moe_layer.post_attention_layernorm.weight = (
            layer.post_attention_layernorm.weight
        )

        # Attention weights
        moe_layer.self_attn.q_proj = layer.self_attn.q_proj
        moe_layer.self_attn.k_proj = layer.self_attn.k_proj
        moe_layer.self_attn.v_proj = layer.self_attn.v_proj
        moe_layer.self_attn.o_proj = layer.self_attn.o_proj

        # FFNs
        if isinstance(moe_layer.mlp, Qwen2MoeSparseMoeBlock):
            # Copy shared expert weights from the dense Qwen model.
            moe_layer.mlp.shared_expert.gate_proj = layer.mlp.gate_proj
            moe_layer.mlp.shared_expert.up_proj = layer.mlp.up_proj
            moe_layer.mlp.shared_expert.down_proj = layer.mlp.down_proj

            with torch.no_grad():
                for expert_mlp in moe_layer.mlp.experts:
                    expert_mlp.gate_proj.weight.mul_(0.0)
                    expert_mlp.up_proj.weight.mul_(0.0)
                    expert_mlp.down_proj.weight.mul_(0.0)
        else:
            # Not expert layer, just copy the weights.
            moe_layer.mlp.gate_proj = layer.mlp.gate_proj
            moe_layer.mlp.up_proj = layer.mlp.up_proj
            moe_layer.mlp.down_proj = layer.mlp.down_proj
    return moe_model


def from_moes_to_moe(moe_models: Sequence[Qwen2MoeForCausalLM]) -> Qwen2MoeForCausalLM:
    num_experts = sum([moe_model.config.num_experts for moe_model in moe_models])
    moe_model = moe_models[0]
    combined_moe = Qwen2MoeConfig(
        **moe_model.config,
        num_experts=num_experts,
    )

    # Copy embeddings & normalization layer.
    combined_moe.set_input_embeddings(moe_model.get_input_embeddings())
    combined_moe.set_output_embeddings(moe_model.get_output_embeddings())
    combined_moe.model.norm.weight = moe_model.model.norm.weight

    # Copy all decoder layer parameters.
    for moe_layer, layer in zip(combined_moe.model.layers, moe_model.model.layers):
        # Layer norms
        moe_layer.input_layernorm.weight = layer.input_layernorm.weight
        moe_layer.post_attention_layernorm.weight = (
            layer.post_attention_layernorm.weight
        )

        # Attention weights
        moe_layer.self_attn.q_proj = layer.self_attn.q_proj
        moe_layer.self_attn.k_proj = layer.self_attn.k_proj
        moe_layer.self_attn.v_proj = layer.self_attn.v_proj
        moe_layer.self_attn.o_proj = layer.self_attn.o_proj

        # FFNs
        if isinstance(moe_layer, Qwen2MoeSparseMoeBlock):
            # Copy shared expert weights from the dense Qwen model.
            moe_layer.mlp.shared_expert.gate_proj = layer.mlp.gate_proj
            moe_layer.mlp.shared_expert.up_proj = layer.mlp.up_proj
            moe_layer.mlp.shared_expert.down_proj = layer.mlp.down_proj

            experts_ = []
            gating_ = []
            for moe in moe_models:
                experts_.extend(moe.mlp.experts)
                gating_.append(moe.mlp.gate.weight)
            moe_layer.mlp.experts = torch.nn.ModuleList(experts_)
            # shape of the projection weights are (num experts, hidden size)
            moe_layer.mlp.gate.weight = torch.cat(gating_, dim=0)
        else:
            # Not expert layer, just copy the weights.
            moe_layer.mlp.gate_proj = layer.mlp.gate_proj
            moe_layer.mlp.up_proj = layer.mlp.up_proj
            moe_layer.mlp.down_proj = layer.mlp.down_proj
    return combined_moe


def expert_state_dict(moe_model: Qwen2MoeForCausalLM) -> dict:
    state_dict = {}
    for (
        index,
        layer,
    ) in enumerate(moe_model.model.layers):
        if not isinstance(layer, Qwen2MoeSparseMoeBlock):
            continue
        key = f"model.layers.{index}.mlp"
        state_dict[key + ".gate"] = layer.mlp.gate.state_dict()
        state_dict[key + ".experts"] = layer.mlp.experts.state_dict()
    return state_dict
