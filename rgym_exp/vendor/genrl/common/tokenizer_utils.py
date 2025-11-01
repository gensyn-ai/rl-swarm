from typing import Any

import torch


def _filter_pad_bos_and_eos(
    tokens: torch.LongTensor, tokenizer: Any
) -> torch.LongTensor:
    mask = torch.logical_and(
        tokens != tokenizer.bos_token_id,
        tokens != tokenizer.eos_token_id,
    )
    if tokenizer.pad_token_id is not None:
        mask = torch.logical_and(
            mask,
            tokens != tokenizer.pad_token_id,
        )
    return tokens[mask]


def _get_attention_mask(
    t: torch.Tensor, padding_side: str, length: int
) -> torch.Tensor:
    if t.shape[-1] == length:
        return torch.ones_like(t)
    else:
        if padding_side == "right":
            return torch.cat(
                [
                    torch.ones_like(t),
                    torch.zeros(
                        (1, (length - t.shape[-1])), dtype=t.dtype, device=t.device
                    ),
                ],
                dim=-1,
            )
        else:
            return torch.cat(
                [
                    torch.zeros(
                        (1, (length - t.shape[-1])), dtype=t.dtype, device=t.device
                    ),
                    torch.ones_like(t),
                ],
                dim=-1,
            )


def _pad(
    t: torch.Tensor, pad_token_id: int | float, padding_side: str, length: int
) -> torch.Tensor:
    if t.shape[-1] == length:
        return t
    else:
        if padding_side == "right":
            return torch.cat(
                [
                    t,
                    torch.tensor(
                        [[pad_token_id] * (length - t.shape[-1])],
                        dtype=t.dtype,
                        device=t.device,
                    ),
                ],
                dim=-1,
            )
        else:
            return torch.cat(
                [
                    torch.tensor(
                        [[pad_token_id] * (length - t.shape[-1])],
                        dtype=t.dtype,
                        device=t.device,
                    ),
                    t,
                ],
                dim=-1,
            )


def decode_and_remove_padding(
    input_ids: torch.LongTensor, tokenizer: Any
) -> list[list[str]]:
    batch = input_ids.unbind(dim=0)
    return [
        [
            tokenizer.decode(_filter_pad_bos_and_eos(tokens, tokenizer).tolist())
            for tokens in hypothesis.unbind(dim=0)
        ]
        for hypothesis in batch
    ]


def tokenize_stages(
    text: list[list[str]],
    tokenizer: Any,
    padding_side: str = "right",
    mask_first_stage: bool = True,
) -> tuple[torch.LongTensor, torch.LongTensor, torch.LongTensor, torch.LongTensor]:
    batch_input_ids = []
    batch_labels = []
    batch_turns = []
    max_length = 0
    for index, stages in enumerate(text):
        tokens = [tokenizer.encode(stage, return_tensors="pt") for stage in stages]
        turns = [
            index * torch.ones_like(turn_tokens)
            for index, turn_tokens in enumerate(tokens)
        ]
        input_ids = torch.cat(tokens, dim=-1)
        turn_ids = torch.cat(turns, dim=-1)
        batch_input_ids.append(input_ids)
        batch_turns.append(turn_ids)
        if mask_first_stage and index == 0:
            labels = tokenizer.pad_token_id * torch.ones_like(input_ids)
        else:
            labels = torch.cat(
                [
                    input_ids[..., 1:],
                    torch.tensor([[tokenizer.eos_token_id]], dtype=torch.int64),
                ],
                dim=-1,
            )
            labels[labels == tokenizer.bos_token_id] = tokenizer.eos_token_id
        batch_labels.append(labels)

        max_length = max(max_length, input_ids.shape[-1])

    return (
        torch.cat(
            [
                _pad(t, tokenizer.pad_token_id, padding_side, max_length)
                for t in batch_input_ids
            ],
            dim=0,
        ),
        torch.cat(
            [
                _pad(t, tokenizer.pad_token_id, padding_side, max_length)
                for t in batch_labels
            ],
            dim=0,
        ),
        torch.cat(
            [_get_attention_mask(t, padding_side, max_length) for t in batch_input_ids],
            dim=0,
        ),
        torch.cat([_pad(t, 0, padding_side, max_length) for t in batch_turns], dim=0),
    )


def pad_rewards(
    rewards: list[list[float]], padding_reward: float = 0.0
) -> torch.Tensor:
    max_stages = max([len(x) for x in rewards])
    return torch.cat(
        [
            _pad(torch.tensor([rewards_]), padding_reward, "left", max_stages)
            for rewards_ in rewards
        ],
        dim=0,
    )
