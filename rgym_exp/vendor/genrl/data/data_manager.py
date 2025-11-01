import abc
from typing import Any, Dict, List, Tuple


class DataManager(abc.ABC):
    def initialize(self):
        """Optional initialization method."""
        pass

    @abc.abstractmethod
    def get_round_data(self) -> Any:
        """Return a batch of data needed to define the start of a round."""
        pass

    @abc.abstractmethod
    def get_eval_data(self) -> Any:
        """Return iterable to eval data."""
        pass

    @abc.abstractmethod
    def prepare_input(
        self, inputs: Dict[Any, List[List[Tuple[Any]]]]
    ) -> Tuple[Any, Dict[int, Tuple[int, int, int]]]:
        """
        Maps agents' world states from their game trees to the format needed by a model to tokenize, ingest, etc.
        Returns:
                - Dataset that the trainer can directly consume and use for generation, training, etc. (maybe with some light preprocessing such as applying a tokenizer.)
                - A dict mapping indices in the newly prepared dataset to indices needed for the game state to correctly opperate on the game tree (i.e., an agent index+a round data batch index+a node index)
        """
        pass

    @abc.abstractmethod
    def prepare_actions(
        self, outputs: Any, index_mapping: Dict[int, Tuple[Any]]
    ) -> Dict[Any, List[List[Any]]]:
        """
        Maps model outputs back to the format needed by the GameState to update agents' game trees with the stage's actions.
        Returns a dict with keys for agents, with list per batch item, with list for each node from this stage in the game tree that contains the output from the trainer.
        """
        pass

    @abc.abstractmethod
    def prepare_states(self, swarm_states: Any) -> Dict[Any, List[List[Tuple[Any]]]]:
        """
        Maps states received via communication with the swarm to the format needed by the GameState to update agents' game trees with the world state at the start of next stage.
        Returns a dict with keys for agents, with list per batch item, with list for each node from this stage in the game tree, with a tuple containing the {environment, opponent, personal}-states.
        """
        pass


class TokenizedDataManager(DataManager):  # TODO: Remove during spring cleaning
    @abc.abstractmethod
    def encode(self, text: str) -> Any:
        pass

    @abc.abstractmethod
    def decode(self, tokens: Any) -> str:
        pass
