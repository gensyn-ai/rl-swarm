import abc
from typing import Any, List

from rgym_exp.vendor.genrl.data import DataManager
from rgym_exp.vendor.genrl.rewards import RewardManager
from rgym_exp.vendor.genrl.state import GameState


# TODO: Update to mirror discussions --> Should be able to directly accept inputs from state in the predefined format and then tokenize+generate+etc. and then produce output in the predefined format so state is able to parse/append/work with output
# NOTE: Predefined format is Dict[List[List[Tuple[Any]]]] where indices correspond to the following [Agents][Batch][Node Idx in Stage][World State]
# NOTE: For output, probably don't need that final dimension since actions/outputs are treated as a singleton item in game tree nodes (regardless of how "complex" the datastructure a single model's rollout is)
class TrainerModule(abc.ABC):
    @abc.abstractmethod
    def __init__(self, models: List[Any], **kwargs):
        pass

    @abc.abstractmethod
    def generate(self, inputs: Any) -> Any:
        pass

    @abc.abstractmethod
    def train(self, game_state: GameState, reward_manager: RewardManager) -> None:
        pass

    @abc.abstractmethod
    def evaluate(
        self, data_manager: DataManager, reward_manager: RewardManager
    ) -> None:
        pass

    @abc.abstractmethod
    def save(self, save_dir: str) -> None:
        pass

    @classmethod
    @abc.abstractmethod
    def load(cls, load_dir: str) -> "TrainerModule":
        pass

    def cleanup(self):
        pass
