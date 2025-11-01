from collections import defaultdict
from copy import deepcopy
from itertools import chain

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, Qwen2ForCausalLM

from rgym_exp.vendor.genrl.common.tokenizer_utils import (
    decode_and_remove_padding,
    pad_rewards,
    tokenize_stages,
)
from rgym_exp.vendor.genrl.data.data_manager import DataManager
from rgym_exp.vendor.genrl.models.moe import Qwen2MoeForCausalLM
from rgym_exp.vendor.genrl.models.moe.moe_helpers import from_qwen_to_moe
from rgym_exp.vendor.genrl.rewards import RewardManager
from rgym_exp.vendor.genrl.state.game_state import GameState
from rgym_exp.vendor.genrl.trainer.base_trainer import TrainerModule


def _compute_grpo_advantages(
    rewards: list[list[list[float]]],
) -> list[list[list[float]]]:
    responses = len(rewards)
    batches = len(rewards[0])

    cumulative_rewards = [defaultdict(lambda: 0) for i in range(batches)]
    response_counts = [defaultdict(lambda: 0) for i in range(batches)]

    # Compute the cumulative reward for every round and stage.
    for i in range(batches):
        for j in range(responses):
            for k in range(len(rewards[j][i])):
                cumulative_rewards[i][k] += rewards[j][i][k]
                response_counts[i][k] += 1

    # Compute mean reward for every round and stage across all responses
    # for the round and stage.
    for i in range(batches):
        for k in cumulative_rewards[i]:
            cumulative_rewards[i][k] /= response_counts[i][k]

    advantages = deepcopy(rewards)
    for i in range(batches):
        for j in range(responses):
            for k in range(len(rewards[j][i])):
                advantages[j][i][k] -= cumulative_rewards[i][k]
    return advantages


class MixtureOfExpertsTrainer(TrainerModule):
    def __init__(
        self,
        model_path_or_name: str,
        tokenizer_path_or_name: str,
        epsilon_low: float,
        epsilon_high: float,
        access_token: str | None = None,
        num_return_sequences: int = 1,
        max_new_tokens: int = 1024,
        **kwargs,
    ):
        self.tokenizer_path_or_name = tokenizer_path_or_name
        self.epsilon_low = epsilon_low
        self.epsilon_high = epsilon_high
        self.num_return_sequences = num_return_sequences
        self.max_new_tokens = max_new_tokens
        self.access_token = access_token
        self.gradient_clip_norm: float | None = kwargs.get("gradient_clip_norm", None)

        try:
            _model = AutoModelForCausalLM.from_pretrained(model_path_or_name)
            if isinstance(_model, Qwen2ForCausalLM):
                self._model = from_qwen_to_moe(
                    _model,
                    num_experts=1,
                    num_experts_per_tok=kwargs["num_experts_per_tok"],
                    moe_intermediate_size=kwargs.get("moe_intermediate_size", None),
                )
            else:
                raise RuntimeError("")
        except:
            self._model = Qwen2MoeForCausalLM.from_pretrained(model_path_or_name)
        self.optimizer = torch.optim.Adam(
            self._model.parameters(), lr=kwargs.get("lr", 1e-4)
        )

    def synchronize_gradients(self):
        pass

    @property
    def tokenizer(self):
        tokenizer = AutoTokenizer.from_pretrained(
            self.tokenizer_path_or_name,
            token=self.access_token,
        )
        if tokenizer.pad_token_id is None:
            setattr(tokenizer, "pad_token_id", tokenizer.bos_token_id)
        return tokenizer

    def generate(self, inputs: list[list[list[str]]]):
        input_ids, _, attention_mask, _ = tokenize_stages(
            list(chain(*inputs)), self.tokenizer, padding_side="left"
        )
        prompt_length = input_ids.shape[-1]
        outputs = self._model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            num_return_sequences=self.num_return_sequences,
            do_sample=True,
            max_new_tokens=self.max_new_tokens,
            return_dict_in_generate=True,
        )
        generated_output = outputs.sequences[..., prompt_length:].view(
            input_ids.shape[0], self.num_return_sequences, -1
        )
        return decode_and_remove_padding(generated_output, tokenizer=self.tokenizer)

    def train(self, game_state: GameState, reward_manager: RewardManager) -> None:
        self.optimizer.zero_grad()
        input_ids, labels, attention_mask, turn_ids = tokenize_stages(
            list(chain(*game_state.outputs)), self.tokenizer, padding_side="right"
        )

        # Assumed as [agent][batch][stage]
        rewards = reward_manager()
        advantages = _compute_grpo_advantages(rewards)
        advantage_tensor = pad_rewards(list(chain(*advantages)), 0.0)
        lm_outputs = self._model(input_ids=input_ids, attention_mask=attention_mask)
        logits = lm_outputs.logits
        loss_mask = (labels == self.tokenizer.pad_token_id).to(dtype=logits.dtype)
        log_probs = torch.nn.functional.cross_entropy(
            logits.view(-1, logits.shape[-1]),
            labels.view(-1),
            reduction="none",
        ).view(logits.shape[0], logits.shape[1])

        token_advantage = torch.stack(
            [
                advantage_[turn_ids_]
                for advantage_, turn_ids_ in zip(
                    advantage_tensor.unbind(dim=0), turn_ids.unbind(dim=0)
                )
            ],
            dim=0,
        )

        # Normalized token probability.
        loss1 = torch.exp(log_probs - log_probs.detach())

        # Loss clipping
        loss2 = torch.clamp(
            loss1, min=1.0 - self.epsilon_low, max=1.0 + self.epsilon_high
        )

        # Per token loss
        token_loss = -loss_mask * token_advantage * torch.min(loss1, loss2)

        # Average per token loss over all valid tokens and take the mean over all responses.
        loss = (token_loss.sum(dim=-1) / loss_mask.sum(dim=-1)).mean()
        loss.backward()

        self.synchronize_gradients()
        if self.gradient_clip_norm is not None:
            torch.nn.utils.clip_grad_norm_(
                self._model.parameters(), self.gradient_clip_norm
            )
        self.optimizer.step()

    def evaluate(self, data_manager: DataManager, reward_manager: RewardManager):
        # TODO(jkolehm): implement evaluation.
        pass

    def save(self, save_dir: str) -> None:
        self._model.save_pretrained(save_dir)

    @classmethod
    def load(cls, load_dir: str) -> "TrainerModule":
        return cls(path=load_dir)
