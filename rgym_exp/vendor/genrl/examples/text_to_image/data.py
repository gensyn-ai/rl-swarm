from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
from torch.utils.data import DataLoader, Dataset

from rgym_exp.vendor.genrl.data.data_manager import DataManager
from rgym_exp.vendor.genrl.examples.text_to_image.ddpo_trainer import DDPOSample
from rgym_exp.vendor.genrl.misc_utils.utils import generate_md5_hash_id
from rgym_exp.vendor.genrl.state import GameState, WorldState


class RandomPromptDataset(Dataset):
    def __init__(self, path):
        with open(path) as f:
            dataset = f.readlines()
        self.dataset = [line.strip() for line in dataset]

    def __call__(self):
        return np.random.choice(self.dataset)

    def __getitem__(self, idx):
        return self.dataset[idx]

    def __len__(self):
        return len(self.dataset)


def custom_collate_fn(batch: List[str]) -> List[Tuple[str, WorldState]]:
    """Collates batches into (list_of_prompts, single_metadata_dict)."""
    prompts = [
        (
            generate_md5_hash_id(item),
            WorldState(
                environment_states=item, opponent_states=None, personal_states=None
            ),
        )
        for item in batch
    ]  # env state, opponent state, personal state
    return prompts


class LocalDatasetManager(DataManager):
    def __init__(
        self,
        train_dataset_path,
        eval_dataset_path,
        train_batch_size: int = 10,
        num_eval_samples: int = 1,
        sample_num_batches_per_round: int = 1,
        **kwargs,
    ):
        train_dataset = RandomPromptDataset(train_dataset_path)
        eval_dataset = RandomPromptDataset(eval_dataset_path)
        self.train_dataloader = DataLoader(
            train_dataset,
            batch_size=train_batch_size,
            shuffle=True,
            drop_last=True,
            collate_fn=custom_collate_fn,  # Use custom collate function
        )
        self.eval_dataloader = DataLoader(
            eval_dataset,
            batch_size=num_eval_samples,
            shuffle=False,
            drop_last=True,
            collate_fn=custom_collate_fn,  # Use custom collate function
        )
        # self.sample_num_batches_per_round = sample_num_batches_per_round
        self._train_iterator = None

        self.num_transplant_trees = kwargs.get("num_transplant_trees", 1)

    def train_batch(self):
        if self._train_iterator is None:
            self._train_iterator = iter(self.train_dataloader)

        try:
            return next(self._train_iterator)

        except StopIteration:
            self._train_iterator = iter(self.train_dataloader)
            return next(self._train_iterator)

    def get_round_data(self):
        return self.train_batch()

    def get_eval_data(self, name: str | None = None):
        return self.eval_dataloader

    def prepare_input(self, inputs: Dict[Any, List[List[Tuple[Any]]]], stage: int):
        batch, index_mapping = [], {}
        cur_idx = 0
        for agent in inputs:
            for batch_id in inputs[agent]:
                for node_idx, state in enumerate(inputs[agent][batch_id]):
                    batch.append(state.environment_states)
                    index_mapping[cur_idx] = (agent, batch_id, node_idx)
                    cur_idx += 1
        return batch, index_mapping

    def prepare_actions(
        self, outputs: Any, index_mapping: Dict[int, Tuple[Any]]
    ) -> Dict[Any, List[List[Any]]]:
        actions = defaultdict(list)

        for idx in range(outputs.prompt_embeds.shape[0]):
            agent, batch_idx, node_idx = index_mapping[idx]
            if agent not in actions:
                actions[agent] = {}
            if batch_idx not in actions[agent]:
                actions[agent][batch_idx] = {}
            single_sample = DDPOSample(
                prompts=outputs.prompts[idx],
                images=outputs.images[idx],
                prompt_embeds=outputs.prompt_embeds[idx],
                timesteps=outputs.timesteps[idx],
                latents=outputs.latents[idx],
                next_latents=outputs.next_latents[idx],
                log_probs=outputs.log_probs[idx],
                negative_prompt_embeds=outputs.negative_prompt_embeds[idx],
            )
            actions[agent][batch_idx][node_idx] = single_sample
        return actions

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
                payload_batch_id = generate_md5_hash_id(world_state)
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
        hashed_trees = [generate_md5_hash_id(str(key[1])) for key in transplants]
        deterministic_scrambled_trees = [
            key for _, key in sorted(zip(hashed_trees, transplants))
        ]
        return {
            key: transplants[key]
            for key in deterministic_scrambled_trees[:num_transplants]
        }
