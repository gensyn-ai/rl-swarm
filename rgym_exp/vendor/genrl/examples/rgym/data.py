import os
from typing import Any, Dict, List, Optional, Tuple

from datasets import Dataset
from reasoning_gym.composite import CompositeConfig, CompositeDataset
from reasoning_gym.dataset import ReseedingDataset
from reasoning_gym.utils import SYSTEM_PROMPTS

from rgym_exp.vendor.genrl.data import LocalMemoryTextDataManager
from rgym_exp.vendor.genrl.examples.rgym.reward_utils import accuracy_reward
from rgym_exp.vendor.genrl.logging_utils.global_defs import get_logger
from rgym_exp.vendor.genrl.misc_utils.utils import generate_md5_hash_id
from rgym_exp.vendor.genrl.state import GameState, WorldState


class ReasoningGymDataManager(LocalMemoryTextDataManager):
    """Data Manager for Reasoning Gym Datasets.

    This class integrates reasoning-gym's composite datasets with genrl
    data management framework, providing infinite iteration through reseeding.
    """

    def __init__(
        self,
        yaml_config_path: str,
        num_train_samples: Optional[int] = None,
        num_evaluation_samples: Optional[int] = None,
        eval_split_ratio: float = 0.2,
        seed: Optional[int] = None,
        batch_item_id_column: Optional[str] = "question",
        system_prompt_id: str = "default",
        chunk_size: int = 500,
        **kwargs,
    ):
        """Initialize the ReasoningGymDataManager.

        Args:
            yaml_config_path: Path to the YAML configuration file for the composite dataset
            num_train_samples: Number of samples to use for training
            num_evaluation_samples: Number of samples to use for evaluation
            eval_split_ratio: Ratio of data to use for evaluation if num_evaluation_samples is None
            seed: Random seed for reproducibility
            batch_item_id_column: Column to use for batch item ID generation
            system_prompt_id: ID of system prompt from reasoning_gym.utils.SYSTEM_PROMPTS
            chunk_size: Size of chunks for ReseedingDataset
        """
        super().__init__(
            train_dataset=None,
            evaluation_dataset=None,
            num_train_samples=num_train_samples,
            num_evaluation_samples=num_evaluation_samples,
            column_name_map={
                "question": "question",
                "answer": "answer",
                "metadata": "metadata",
            },
            column_preprocessing_map=None,
            seed=seed,
            batch_item_id_column=batch_item_id_column,
            data_generator=self.load_reasoning_gym_dataset,  # TODO: this was confusing, we should document or change the way this is done
        )

        self.yaml_config_path = yaml_config_path
        self.eval_split_ratio = eval_split_ratio
        self.chunk_size = chunk_size
        self.system_prompt = SYSTEM_PROMPTS.get(
            system_prompt_id, SYSTEM_PROMPTS["default"]
        )
        self.num_transplant_trees = kwargs.get("num_transplant_trees", 1)
        assert self.num_transplant_trees >= 0

        try:
            self.config = CompositeConfig.from_yaml(yaml_config_path)

            if seed is not None:
                self.config.seed = seed

            self.composite_dataset = CompositeDataset(self.config)

            self.reseeding_dataset = ReseedingDataset(
                self.composite_dataset, chunk_size=self.chunk_size
            )

            self._create_dataset_splits()

        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize ReasoningGymDataManager: {str(e)}"
            )

        self.initialize()

    def _create_dataset_splits(self):
        """Create train/eval dataset splits"""
        total_samples = len(self.composite_dataset)

        if self.num_samples["evaluation"] is None:
            eval_count = int(total_samples * self.eval_split_ratio)
        else:
            eval_count = min(self.num_samples["evaluation"], total_samples)

        if self.num_samples["train"] is None:
            train_count = total_samples - eval_count
        else:
            train_count = min(self.num_samples["train"], total_samples - eval_count)

        self.num_samples["train"] = train_count
        self.num_samples["evaluation"] = eval_count

    def load_reasoning_gym_dataset(
        self,
        dataset_id_or_path: Optional[str] = None,
        subset: Optional[str] = None,
        split: Optional[str] = "train",
        num_samples: Optional[int] = None,
    ) -> Dataset:
        """Load the reasoning gym dataset from the reseeding dataset.

        This overrides the parent class's load_HF_dataset method.

        Args:
            dataset_id_or_path: Ignored, using reseeding dataset
            subset: Ignored, using reseeding dataset
            split: 'train' or 'test' to determine which split to use
            num_samples: Number of samples to use

        Returns:
            A Dataset object containing the samples from the reseeding dataset
        """
        dataset_dict = {"question": [], "answer": [], "metadata": []}

        if split in ("test", "validation"):
            max_samples = self.num_samples["evaluation"]
        else:  # Default to train
            max_samples = self.num_samples["train"]

        if num_samples is not None:
            max_samples = min(num_samples, max_samples)

        for i in range(max_samples):
            item = next(self.reseeding_dataset)

            idx = i

            dataset_dict["question"].append(item["question"])
            dataset_dict["answer"].append(item["answer"])

            metadata = item.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {"original_metadata": metadata}

            metadata["dataset_index"] = idx
            metadata["split"] = split

            dataset_dict["metadata"].append(metadata)

        return Dataset.from_dict(dataset_dict)

    # --- Helper Methods ---
    def state_to_system_prompt(self, state: WorldState) -> str:
        """Return the system prompt for the reasoning task."""
        return self.system_prompt

    def state_to_user_prompt(self, state: WorldState) -> str:
        """Convert the state to a user prompt."""
        return state.environment_states["question"]

    def state_to_answer(self, state: WorldState) -> str:
        """Extract the answer from the state."""
        return state.environment_states["answer"]

    # --- Required Methods ---
    def initialize(self):
        """Initialize the data manager."""
        get_logger().info(
            f"Reasoning Gym Data Manager initialized with config: {self.yaml_config_path}"
        )
        get_logger().info(
            f"Loaded composite dataset with {len(self.composite_dataset)} samples"
        )
        get_logger().info(
            f"Train samples: {self.num_samples['train']}, Eval samples: {self.num_samples['evaluation']}"
        )
        get_logger().info(
            f"Dataset weights: {', '.join([f'{name}: {self.config.get_dataset_weight(name)}' for name in self.composite_dataset.datasets])}"
        )

    def flatten_states(
        self, flattened_input: Dict[str, List[Any]], state: WorldState, stage: int
    ) -> Dict[str, WorldState]:
        """Convert the state into a flattened format for the model input."""
        if flattened_input == {}:
            flattened_input = {
                "system_prompt": [],
                "user_prompt": [],
                "answer": [],
                "metadata": [],
            }

        flattened_input["system_prompt"].append(self.state_to_system_prompt(state))
        flattened_input["user_prompt"].append(self.state_to_user_prompt(state))
        flattened_input["answer"].append(self.state_to_answer(state))

        if "metadata" in state.environment_states:
            flattened_input["metadata"].append(state.environment_states["metadata"])
        elif state.metadata is not None:
            flattened_input["metadata"].append(state.metadata)
        else:
            flattened_input["metadata"].append({})

        return flattened_input

    def prepare_environment(
        self,
        node_states: List[Any],
        swarm_states: Dict[Any, Any],
        stage: int,
        agent: Any,
        batch_id: Any,
    ) -> Any:
        """Prepare the environment state for the next stage."""
        pass

    def prepare_opponent(
        self,
        node_states: List[Any],
        swarm_states: Dict[Any, Any],
        stage: int,
        agent: Any,
        batch_id: Any,
    ) -> Any:
        """Prepare the opponent state for the next stage."""
        pass

    def prepare_personal(
        self,
        node_states: List[Any],
        swarm_states: Dict[Any, Any],
        stage: int,
        agent: Any,
        batch_id: Any,
    ) -> Any:
        """Prepare the personal state for the next stage."""
        pass

    def prepare_states(
        self, current_state: GameState, swarm_states: Dict[Any, Any]
    ) -> Dict[Any, Dict[Any, List[Tuple[Any]]]]:
        if self.num_transplant_trees > 0:
            trees = current_state.trees
            transplants = self.transplant_trees(
                current_state, swarm_states, self.num_transplant_trees
            )
            for pair in transplants:
                agent, batch_id = pair
                if agent not in trees:
                    trees[agent] = {}
                if batch_id not in trees[agent]:
                    trees[agent][batch_id] = None
                payload = transplants[pair]
                received_states, received_actions, received_metadata = (
                    payload["world_state"],
                    payload["actions"],
                    payload["metadata"],
                )
                world_state = received_states.environment_states
                payload_batch_id = generate_md5_hash_id(world_state["question"])
                assert payload_batch_id == batch_id
                if (
                    trees[agent][batch_id] is None
                ):  # we don't have a tree for this batch item, make one and append actions
                    trees[agent][batch_id] = current_state.game_tree_factory(
                        received_states
                    )
                    trees[agent][batch_id].append_node_actions(
                        stage=current_state.stage, node_idx=0, actions=received_actions
                    )
                    trees[agent][batch_id][current_state.stage][0][
                        "metadata"
                    ] = received_metadata
                else:  # we already have this tree, and actions were appended in run_game_stage()
                    pass
        world_state = current_state.get_latest_state()
        return world_state

    def transplant_trees(
        self,
        current_state: GameState,
        swarm_states: Dict[Any, Any],
        num_transplants: int,
    ) -> Dict[Tuple[Any], Any]:
        # Loop through and return a set of num_transplant transplants to add
        transplants = {}
        for agent in swarm_states:
            if agent not in current_state.trees:
                for batch_id in swarm_states[agent]:
                    for payload in swarm_states[agent][batch_id]:
                        transplants[(agent, batch_id)] = payload
        total_score_per_tree = [
            sum(
                accuracy_reward(
                    transplants[key]["actions"],
                    transplants[key]["world_state"].environment_states["answer"],
                    transplants[key]["world_state"].environment_states["metadata"],
                )
            )
            for key in transplants
        ]
        sorted_trees = [
            key for _, key in sorted(zip(total_score_per_tree, transplants))
        ]  # TODO(gab): Should we be sorting by avg rather than total score? Should we be filtering by "advantage" rather than bounding score stats?
        try:
            lower_bound_idx_filter = next(
                idx
                for idx, tot_score in enumerate(total_score_per_tree)
                if tot_score != 0
            )
            sorted_trees = sorted_trees[lower_bound_idx_filter:]
            num_transplants = min(num_transplants, len(sorted_trees))
            return {key: transplants[key] for key in sorted_trees[-num_transplants:]}
        except StopIteration:  # All elements of total_score_per_tree are == 0
            return (
                {}
            )  # Default to not taking anything from the swarm, but reasonable alternative might be to do a random sample instead
