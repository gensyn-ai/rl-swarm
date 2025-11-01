from dataclasses import dataclass
from typing import Callable, Iterable


@dataclass
class RoundRewardFnStore:
    """
    Store reward functions for each stage of a round.
    This data structure expects the number of reward functions to match the number of stages.
    """

    num_stages: int
    reward_fns: Iterable[Callable]

    def __post_init__(self) -> None:
        if self.num_stages <= 0:
            raise ValueError("num_stages must be a positive integer")

        # if no reward functions provided, default to null rewards
        # TODO(discuss): Should definitely trigger a big ol' warning to make sure people know they are hitting this case and proceeding anyhow
        if self.reward_fns is None or len(self.reward_fns) == 0:
            self.reward_fns = [lambda x: 0 for _ in range(self.num_stages)]

        if self.reward_fns is not None and len(self.reward_fns) == 1:
            self.reward_fns = [self.reward_fns[0]] * self.num_stages

        if not len(self.reward_fns) == self.num_stages:
            raise ValueError("Number of reward functions must match number of stages")

    def __len__(self) -> int:
        return self.num_stages

    def __getitem__(self, stage: int) -> Callable:
        return self.reward_fns[stage]


@dataclass
class RewardFnStore:
    """
    Store a RoundRewardFnStore for each round of the game, up to the maximum number of rounds.
    This data structure expects the number of RoundRewardFnStore's to match the number of rounds.
    """

    max_rounds: int
    reward_fn_stores: Iterable[RoundRewardFnStore]

    def __post_init__(self) -> None:
        if self.max_rounds is None or self.max_rounds <= 0:
            raise ValueError("max_rounds must be a positive integer")

        # if no reward functions provided, default to single stage with null rewards
        if self.reward_fn_stores is None or len(self.reward_fn_stores) == 0:
            self.reward_fn_stores = [RoundRewardFnStore(1, [])]

        if self.reward_fn_stores is not None and len(self.reward_fn_stores) == 1:
            self.reward_fn_stores = [self.reward_fn_stores[0]] * self.max_rounds

        if not len(self.reward_fn_stores) == self.max_rounds:
            raise ValueError(
                "Number of round reward function stores must match max_rounds"
            )

    def __len__(self) -> int:
        return self.max_rounds

    def __getitem__(self, round: int) -> RoundRewardFnStore:
        return self.reward_fn_stores[round]
