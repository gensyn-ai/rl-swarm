from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Tuple

from rgym_exp.vendor.genrl.communication import Payload
from rgym_exp.vendor.genrl.state.game_tree import DefaultGameTree, WorldState
from rgym_exp.vendor.genrl.logging_utils.global_defs import get_logger


@dataclass
class GameState:
    round: int
    stage: int

    trees: Dict[Any, Dict[int, Callable]] | None = None  # [Agent][Batch][GameTree]
    game_tree_factory: Callable = (
        DefaultGameTree  # GameTree data structure to use for building tree
    )

    def __post_init__(self) -> None:
        if self.round < 0:
            self.round = 0
        if self.stage < 0:
            self.stage = 0
        self.world_state_pruners = {
            "environment_pruner": None,
            "opponent_pruner": None,
            "personal_pruner": None,
        }
        self.tree_branching_functions = {
            "terminal_node_decision_function": None,
            "stage_inheritance_function": None,
        }

    def _init_game(
        self,
        round_data: List[Tuple[str, WorldState]],
        agent_keys: List[Any] = [0],
        world_state_pruners: Dict[str, Callable | None] = None,
        game_tree_brancher: Dict[str, Callable | None] = None,
    ) -> None:
        """
        For each agent this builds a game tree with only a root for each datum in the round_data batch.
        Assumes all agents on this device will operate on the same round_data.

        NOTE: Will hash input data for making sure game trees get updates with only relevant round_data when communicating across the swarm.

        Inputs:
            List[Tuple[Any]]: List containing tuples of world state needed for defining an agent's input for this device. Each Tuple of world states has the form (state_key_metadata, environment_states, opponent_states, personal_states)
            List[Any]: List containing agent keys for each agent that will be "hosted" on this device
        """
        if world_state_pruners is not None:
            self.world_state_pruners = world_state_pruners  # Game-specific pruner functions for passing to game trees. Defines what state details are relevant to a stage + should be broacast. NOTE: Using None here means no pruning of that type of state!
        if game_tree_brancher is not None:
            self.tree_branching_functions = game_tree_brancher  # Game-specific functions for passing to game trees to define when they should consider a node "terminal" + when/how a node should be branched to produce children

        self.batch_size = len(round_data)

        get_logger().debug(f"[DEBUG_TREES] _init_game called: round={self.round}, stage={self.stage}, batch_size={self.batch_size}, agent_keys={agent_keys}")

        self.trees = {}
        for agent in agent_keys:
            self.trees[agent] = {}
            for batch_idx in range(self.batch_size):
                self.trees[agent][round_data[batch_idx][0]] = self.game_tree_factory(
                    round_data[batch_idx][1]
                )  # NOTE: Assumes round data is a list containting tuples of [unique_id, WorldState]

        tree_counts = {agent: len(self.trees[agent]) for agent in self.trees}
        get_logger().debug(f"[DEBUG_TREES] _init_game completed: trees keys={list(self.trees.keys())}, tree_counts={tree_counts}")

    # Core methods
    def advance_round(
        self, round_data: List[Tuple[str, WorldState]], agent_keys: List[Any] = [0]
    ) -> None:
        """Increments round, restarts stage count, and initializes game tree on the new round's data"""
        self.round += 1
        self.stage = 0
        self._init_game(round_data, agent_keys)

    def get_stage_state(self, stage_num: int) -> Dict[Any, Dict[Any, List[List[Any]]]]:
        """
        Returns required state information for preparing a data batch from the desired stage

        Returns:
            Dict[Dict[List[List[Any]]]]: Dict keyed on agents containing a dict keyed on batch item ids that contains a list for each node for the desired stage.
                                          The list per node in the desired stage contains tuples with state information required for preparing the corresponding agent's data batch for the desired stage.
                                          Tuples have the form (environment_states, opponent_states, personal_states)
        """
        if self.trees and len(self.trees) > 0:
            agents = {}
            for agent in self.trees:
                agents[agent] = {}
                for batch_id in self.trees[agent]:
                    agents[agent][batch_id] = []
                    batch_nodes = self.trees[agent][batch_id][stage_num]
                    for node_idx in range(len(batch_nodes)):
                        world_state = batch_nodes[node_idx].world_state
                        agents[agent][batch_id].append(world_state)
            return agents  # [Agents][Batch][Node Idx in Stage][World State]
        else:
            raise RuntimeError(
                "Trying to get game state information, but game trees are not defined."
            )

    def get_stage_actions(self, stage_num: int) -> Dict[Any, Dict[Any, List[Any]]]:
        """
        Returns actions stored in the nodes of a stage
        NOTE: Behaves similarly to get_stage_state, but loses a dimension since actions are a singleton object within nodes. That said, they can be any type depending on game specifics.

        Returns:
            Dict[Dict[List[Any]]]: Dict keyed on agents containing a dict keyed on batch item ids that contains a list for each node for the desired stage.
                                   The list per node in the desired stage contains actions for said node.
        """
        if self.trees and len(self.trees) > 0:
            agents = {}
            for agent in self.trees:
                agents[agent] = {}
                for batch_id in self.trees[agent]:
                    agents[agent][batch_id] = []
                    batch_nodes = self.trees[agent][batch_id][stage_num]
                    for node_idx in range(len(batch_nodes)):
                        actions = batch_nodes[node_idx].actions
                        agents[agent][batch_id].append(actions)
            return agents  # [Agents][Batch][Node Idx in Stage]
        else:
            raise RuntimeError(
                "Trying to get game state information, but game trees are not defined."
            )

    def get_stage_communication(
        self, stage_num: int
    ) -> Dict[Any, Dict[Any, List[Payload]]]:
        """
        Returns a communication payload for the specified stage of the game.

        Returns:
            Dict[Dict[Payload]]: Dict keyed on agents containing a dict keyed on batch item ids that contains a list with a communication payload for each node in the desired stage.
        """
        if self.trees and len(self.trees) > 0:
            agents = {}
            for agent in self.trees:
                agents[agent] = {}
                for batch_id in self.trees[agent]:
                    agents[agent][batch_id] = []
                    batch_nodes = self.trees[agent][batch_id][stage_num]
                    for node_idx in range(len(batch_nodes)):
                        world_state = batch_nodes[node_idx].world_state
                        actions = batch_nodes[node_idx].actions
                        metadata = batch_nodes[node_idx].metadata
                        payload = Payload(
                            world_state=world_state, actions=actions, metadata=metadata
                        )
                        agents[agent][batch_id].append(payload)
            return agents  # [Agents][Batch][Node Idx in Stage][World State]
        else:
            raise RuntimeError(
                "Trying to get game state information, but game trees are not defined."
            )

    def get_latest_state(self) -> Dict[Any, Dict[Any, List[List[Any]]]]:
        """Get stage state for current stage of the game"""
        return self.get_stage_state(
            self.stage
        )  # [Agents][Batch][Nodes in Current Stage][World State]

    def get_latest_actions(self) -> Dict[Any, Dict[Any, List[Any]]]:
        """Get stage state for current stage of the game"""
        return self.get_stage_actions(
            self.stage
        )  # [Agents][Batch][Node Idx in Current Stage]

    def get_latest_communication(self) -> Dict[Any, Dict[Any, List[Payload]]]:
        """Prepare communication payload dataclass for current stage of the game"""
        return self.get_stage_communication(
            self.stage
        )  # [Agents][Batch][Nodes in Current Stage][World State]

    def append_actions(self, agent_actions: Dict[Any, List[List[Any]]]) -> None:
        """
        Takes outputs generated/made by an agent and appends it to the corresponding nodes
        At a high-level this method performs the following operations:
            1. Updates the generations to appropriate nodes
            2. Create nodes for the next stage and fill their round states as much as possible
        """
        if self.trees and len(self.trees) > 0:
            for agent in self.trees:
                for batch_id in self.trees[agent]:
                    for node_idx in range(len(agent_actions[agent][batch_id])):
                        self.trees[agent][batch_id].append_node_actions(
                            stage=self.stage,
                            node_idx=node_idx,
                            actions=agent_actions[agent][batch_id][node_idx],
                        )  # Append rollout to current node
                    self.trees[agent][batch_id].commit_actions_from_stage(
                        stage=self.stage,
                        tree_branching_functions=self.tree_branching_functions,
                    )  # Signals that the agent is "done" with this tree for this stage+makes children and/or sets nodes as terminal.
        else:
            raise RuntimeError(
                "Trying to update game trees, but game trees are not defined."
            )

    def advance_stage(self, world_states: Dict[Any, List[List[Tuple[Any]]]]) -> None:
        """
        Updates tree node states of next stage after having communicated, then increments the stage.
        """
        if self.trees and len(self.trees) > 0:
            self.stage += 1  # Increment stage
            for agent in self.trees:
                for batch_id in self.trees[agent]:
                    stage_nodes = self.trees[agent][batch_id][self.stage]
                    for node_idx in range(len(stage_nodes)):
                        self.trees[agent][batch_id].append_node_states(
                            stage=self.stage,
                            node_idx=node_idx,
                            states=world_states[agent][batch_id][node_idx],
                            pruning_functions=self.world_state_pruners,
                        )  # Assumes new stage's nodes relevant to a parent were created at the moment when we "commited" during append generation
        else:
            raise RuntimeError(
                "Trying to update game trees, but game trees are not defined."
            )
