import enum
from typing import Iterable

import torch
import torch.distributed as dist
import torch.nn.functional as F
from transformers.generation import GenerateDecoderOnlyOutput


class GenerationMethod(enum.Enum):
    BEAM_SEARCH = "beam_search"
    SAMPLING = "sampling"


PastKeyValuesType = tuple[tuple[torch.Tensor, torch.Tensor]]


def _get_tokens(
    logits: torch.Tensor,
    k: int,
    temperature: float,
    method: GenerationMethod,
) -> tuple[torch.Tensor, torch.LongTensor]:
    # Take the last tokens logits.
    logits = logits[..., -1, :]
    log_probs = F.log_softmax(logits / temperature, dim=-1)
    if method == GenerationMethod.BEAM_SEARCH:
        log_probs_, idx = torch.topk(log_probs, k=k, dim=-1)
        return log_probs_, idx
    elif method == GenerationMethod.SAMPLING:
        probs = torch.exp(log_probs.float())
        probs_shape = probs.shape
        idx = torch.multinomial(probs.view(-1, probs.shape[-1]), k)
        idx = idx.view(*probs_shape[:-1], k)
        return torch.gather(log_probs.to(dtype=logits.dtype), index=idx, dim=-1), idx
    else:
        raise ValueError(f"Unknown generation method: {method}.")


def _update(
    hypothesis: torch.LongTensor,
    log_probs: torch.Tensor,
    new_tokens: torch.LongTensor,
    new_log_probs: torch.Tensor,
    k: int,
    method: GenerationMethod,
) -> tuple[PastKeyValuesType, torch.LongTensor, torch.LongTensor, torch.Tensor]:
    # Reconstruct k^2 hypothesis with shape (batch, k^2, sequence+1)
    new_hypothesis = torch.stack(
        [
            torch.cat(
                [
                    torch.stack(
                        [
                            torch.cat([hyp_, token.unsqueeze(dim=0)], dim=0)
                            for token in tokens_
                        ],
                        dim=0,
                    )
                    for hyp_, tokens_ in zip(hyps.unbind(dim=0), tokens.unbind(dim=0))
                ],
                dim=0,
            )
            for hyps, tokens in zip(hypothesis.unbind(dim=0), new_tokens.unbind(dim=0))
        ],
        dim=0,
    )
    new_tokens_ = new_tokens.view(new_tokens.shape[0], -1)

    hypothesis_log_probs = torch.stack(
        [
            torch.cat(
                [
                    hyp_log_prob_ + token_log_probs_
                    for hyp_log_prob_, token_log_probs_ in zip(
                        hyp_log_probs.unbind(dim=0), token_log_probs.unbind(dim=0)
                    )
                ],
                dim=0,
            )
            for hyp_log_probs, token_log_probs in zip(
                log_probs.unbind(dim=0), new_log_probs.unbind(dim=0)
            )
        ],
        dim=0,
    )

    if method == GenerationMethod.BEAM_SEARCH:
        log_probs, idx = torch.topk(hypothesis_log_probs, k=k, dim=-1)
    elif method == GenerationMethod.SAMPLING:
        probs = torch.exp(hypothesis_log_probs.float())
        probs_shape = probs.shape
        idx = torch.multinomial(probs.view(-1, probs.shape[-1]), k)
        idx = idx.view(*probs_shape[:-1], k)
        log_probs = torch.gather(
            (hypothesis_log_probs.to(dtype=log_probs.dtype)), index=idx, dim=-1
        )
    else:
        raise ValueError(f"Unknown generation method: {method}.")
    input_ids = torch.gather(new_tokens_, index=idx, dim=-1)
    hypothesis = torch.gather(
        new_hypothesis,
        index=idx.unsqueeze(dim=-1).expand(-1, -1, new_hypothesis.shape[-1]),
        dim=1,
    )
    return input_ids, hypothesis, log_probs


def _create_attention_mask(
    input_ids: torch.LongTensor,
    eos_tokens: Iterable[int],
    attention_mask: torch.Tensor | None = None,
):
    mask = (
        attention_mask > 0.0
        if attention_mask is not None
        else torch.ones_like(input_ids)
    )

    # TODO(jkolehm): ugly but allows using tensors.
    for eos_token in eos_tokens:
        mask = torch.logical_and(mask, input_ids != eos_token)
    return mask


def _insert_padding_tokens(
    logits: torch.Tensor,
    attention_mask: torch.Tensor,
    pad_token_id: int,
):
    mask = attention_mask < 1.0
    logits[mask, range(pad_token_id, pad_token_id + 1)] += torch.finfo(logits.dtype).max
    return logits


def _reshape_past_key_values(past_key_values, shape):
    return tuple(
        [
            (
                layer_past_key_values[0].reshape(*shape),
                layer_past_key_values[1].reshape(*shape),
            )
            for layer_past_key_values in past_key_values
        ]
    )


def moe_generate(self: torch.nn.Module, pg: dist.ProcessGroup | None = None):
    def _fun(
        input_ids: torch.LongTensor,
        attention_mask: torch.Tensor | None = None,
        **kwargs,
    ) -> GenerateDecoderOnlyOutput:
        temperature: float = kwargs.get("temperature", 1.0)
        num_return_sequences = kwargs.get("num_return_sequences", 1)
        max_new_tokens = kwargs.get("max_new_tokens", 16384)
        eos_token_ids = kwargs.get("eos_token_id", [])
        pad_token_id = kwargs.get("pad_token_id", 0)
        return_dict_in_generate = kwargs.get("return_dict_in_generate", False)
        method = (
            GenerationMethod.SAMPLING
            if kwargs.get("generation_config", {}).get("do_sample", False)
            else GenerationMethod.BEAM_SEARCH
        )
        device = input_ids.device
        batch_size = input_ids.shape[0]

        # Compute the initial past-key values
        outputs = self(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits
        log_probs_, tokens_ = _get_tokens(
            logits, num_return_sequences, temperature, method
        )
        input_ids = tokens_.reshape(-1, num_return_sequences, 1)
        hypothesis = input_ids.clone()
        log_probs = log_probs_.reshape(-1, num_return_sequences)
        attention_mask = _create_attention_mask(input_ids, eos_token_ids)
        num_heads = self.config.num_key_value_heads
        head_dim = self.config.hidden_size // self.config.num_attention_heads

        past_key_values = [
            (
                layer_past_key_values[0]
                .unsqueeze(dim=1)
                .expand(-1, num_return_sequences, -1, -1, -1),
                layer_past_key_values[0]
                .unsqueeze(dim=1)
                .expand(-1, num_return_sequences, -1, -1, -1),
            )
            for layer_past_key_values in outputs.past_key_values
        ]

        number_of_tokens_generated = 1

        while number_of_tokens_generated < max_new_tokens:
            # Process is still generating, inform other processes in the PG that they need
            # to call forward in the model.
            dist.all_reduce(
                torch.tensor([1], dtype=torch.int64, device=device),
                group=pg,
                async_op=True,
            )

            # Call forward pass with local data and obtain local outputs.
            with torch.no_grad():
                outputs = self(
                    input_ids=input_ids.view(-1, 1),
                    attention_mask=attention_mask.view(-1, 1),
                    past_key_values=_reshape_past_key_values(
                        past_key_values,
                        (batch_size * num_return_sequences, num_heads, -1, head_dim),
                    ),
                )

            # Reshape outputs and mask logits for sequences that have reached EOS token.
            logits = outputs.logits.reshape(batch_size, num_return_sequences, 1, -1)
            with torch.no_grad():
                logits = _insert_padding_tokens(logits, attention_mask, pad_token_id)
            past_key_values = _reshape_past_key_values(
                outputs.past_key_values,
                (batch_size, num_return_sequences, num_heads, -1, head_dim),
            )

            # Extract tokens from the logits.
            log_probs_, tokens_ = _get_tokens(
                logits, num_return_sequences, temperature, method
            )
            tokens_ = tokens_.view(
                batch_size, num_return_sequences, num_return_sequences
            )
            log_probs_ = log_probs_.view(
                batch_size, num_return_sequences, num_return_sequences
            )

            # Update past-key-values and input_ids for next round
            with torch.no_grad():
                input_ids, hypothesis, log_probs = _update(
                    hypothesis,
                    log_probs,
                    tokens_,
                    log_probs_,
                    num_return_sequences,
                    method,
                )
            attention_mask = _create_attention_mask(
                input_ids, eos_token_ids, attention_mask
            )
            number_of_tokens_generated += 1

            if torch.all(attention_mask < 1.0):
                # All sequences have reached EOS token, exit generation.
                break

        # Make dummy calls to forward until all processes have finished generation.
        while True:
            t = torch.tensor([0], dtype=torch.int64, device=device)
            dist.all_reduce(t, group=pg)

            if t.item() == 0:
                # All processes are done with generation, exit.
                break
            else:
                # Call forward with dummy inputs to participate in the forward call.
                dummy_input_id = torch.tensor(
                    [[pad_token_id]], device=device, dtype=input_ids.dtype
                )
                dummy_mask = torch.tensor(
                    [[0]], device=device, dtype=attention_mask.dtype
                )
                with torch.no_grad():
                    _ = self(input_ids=dummy_input_id, attention_mask=dummy_mask)
        return (
            GenerateDecoderOnlyOutput(sequences=hypothesis, scores=-log_probs)
            if return_dict_in_generate
            else hypothesis
        )

    return _fun
