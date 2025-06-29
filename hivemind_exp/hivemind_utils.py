from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

import torch


@dataclass
class HivemindNode:
    # Node metadata.
    model_name: str
    key: str  # Set to DHT PeerID.

    is_coordinator: bool = False

    # Q&A outputs from the last training step.
    outputs: dict[Any, Any] = field(default_factory=dict)
    # Cache for (r, s): Q: (timestamp, outputs).
    round_cache: dict[tuple[int, int], dict[str, tuple[float, dict]]] = field(
        default_factory=lambda: defaultdict(dict)
    )

    # Reward outputs from the last training.
    rewards: Sequence[float | int] = field(default_factory=list)

    # Values incremented by coordinator.
    round_num: int = 0
    stage_num: int = 0

    out_expiration: int = 60 * 60 * 4  # hours

    @staticmethod
    def coordinator(*args, **kwargs):
        return HivemindNode(*args, **kwargs, is_coordinator=True)

    def get_stage_outputs(self, r, s) -> dict[str, tuple[float, dict]] | None:
        key = (r, s)
        if key in self.round_cache:
            return self.round_cache[key]

    def put_stage_outputs(self, r, s, question, value: tuple[float, dict]):
        self.round_cache[(r, s)][question] = value

    def clear_stage_cache(self):
        self.round_cache.clear()


# Takes round + stage.
DatasetsFn = Callable[
    [int, int], tuple[torch.utils.data.Dataset, torch.utils.data.Dataset]
]

MergeFn = Callable[[list], dict[str, dict]]
LossFn = Callable[[list], dict[str, float]]


@dataclass
class SingleStageData:
    name: str
    reward_funcs: list[Callable]
    datasets_fn: DatasetsFn  # For train / test datasets.


@dataclass
class StageData:
    stages: Sequence[SingleStageData]
    round_winner_fn: Callable

    max_rounds: int = 100
    train_timeout: int = 60 * 60 * 24 * 31  # days
    round_timeout: int = 60 * 60 * 4  # hours

    def __len__(self):
        return len(self.stages)