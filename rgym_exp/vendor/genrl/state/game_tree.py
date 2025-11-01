import abc
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Tuple


@dataclass
class WorldState:
    environment_states: List[Any]
    opponent_states: List[Any]
    personal_states: List[Any]


@dataclass
class GameNode:
    # TODO: Use enum to avoid string case matching
    # TODO: Add a more elegant way of handling world states in nodes
    """
    Keeps track of all data needed for defining a node in the game tree
    Each individual node is capable of storing all required input for a stage and the resultant output
    """
    stage: int  # Stage this node is created for. Places node in the sequence of "time" # NOTE: Should not change after node creation
    node_idx: int  # Unique identifier for this node within its stage. How (and if) this is used will depend on the game being played # NOTE: Should not change after node creation

    parents: List["GameNode"] | None = (
        None  # List of parent nodes. Should only point to nodes within the same GameTree whose actions this node's actions depends on
    )
    children: List["GameNode"] | None = (
        None  # List of child nodes. Should only point to nodes within the same GameTree whose actions depend on this node's actions
    )

    world_state: WorldState = None  # World state at the time of node creation
    actions: Any = (
        None  # Actions taken as a function of {environment, opponent, agent}-states by agent whose game tree this Node exists in
    )
    metadata: Any = (
        None  # Placeholder for storing any additional information, context, etc. that isn't directly used by agents in the game yet is useful for computing metrics, etc.
    )

    def __post_init__(self) -> None:
        # Check that created node conforms to poset ordering or set as empty list
        if self.parents is not None:
            for parent in self.parents:
                if self._breaks_poset_ordering(parent, "Parent"):
                    raise RuntimeError(
                        f"Found a parent from stage {parent.stage}. Current node is from stage {self.stage}. Please ensure parents are from the same stage or earlier!"
                    )
        else:
            self.parents = []

        if self.children is not None:
            for child in self.children:
                if self._breaks_poset_ordering(child, "Child"):
                    raise RuntimeError(
                        f"Found a child from stage {child.stage}. Current node is from stage {self.stage}. Please ensure children are from the same stage or later!"
                    )
        else:
            self.children = []

    def append_child(self, node: "GameNode") -> None:
        if self._breaks_poset_ordering(node, direction="Child") or self._is_leaf_node():
            raise RuntimeError(
                f"Attempting to add a child from stage {node.stage}, but current node is from stage {self.stage} and/or has been designated as a leaf node! Please ensure leaf nodes do not have children and that any children are from the same stage or later."
            )
        else:
            self.children.append(node)

    def append_parent(self, node: "GameNode") -> None:
        if (
            self._breaks_poset_ordering(node, direction="Parent")
            or self._is_root_node()
        ):
            raise RuntimeError(
                f"Attempting to add a parent from stage {node.stage}, current node is from stage {self.stage} and/or has been designated as a root node! Please ensure root nodes do not have parents and that any parents are from the same stage or earlier."
            )
        else:
            self.parents.append(node)

    def set_as_root(self) -> None:
        if not self.parents:
            self.parents = None
        else:
            raise ValueError(
                f"Trying to set a node as a root, but it already has parents! Parents found: {self.parents}"
            )

    def set_as_terminal(self) -> None:
        if not self.children:
            self.children = None
        else:
            raise ValueError(
                f"Trying to set a node as terminal, but it already has children! Children found: {self.children}"
            )

    def _breaks_poset_ordering(self, node: "GameNode", direction: str) -> bool:
        if direction == "Parent":
            return True if (node.stage > self.stage) else False
        elif direction == "Child":
            return True if (node.stage < self.stage) else False
        else:
            raise ValueError(
                f"Specified direction is not recognized. Direction=={direction}"
            )

    def _is_root_node(self) -> bool:
        if self.parents == None:
            return True
        else:
            return False

    def _is_leaf_node(self) -> bool:
        if self.children == None:
            return True
        else:
            return False

    # Methods for emulating a mapping container object
    def __getitem__(self, key):
        return getattr(self, str(key))

    def __setitem__(self, key, value):
        setattr(self, str(key), value)


@dataclass
class GameTree(abc.ABC):
    """
    Defines a directed game tree with nodes partially ordered by stage/turn of the game.
    Nodes should be nearly self-contained descriptors of (world state, agent action) pairs--they either directly contain or are linked to other nodes required for constructing the state of the world which is needed for the agent to produce the actions stored in the node.

    GameTree orchestrates the creation of nodes, populating information within nodes, and management of information across several nodes (e.g., knowing a branch reaches a terminal state)
    GameTree emulates a mapping container type to facilitate calls from the GameManager (through GameState)
    GameTree assumes the set of nodes are IMMUTABLE. Once a node is added it should not be deleted! NOTE: If you choose to do so, then you risk breaking possibly delicate (and vital) causal dependancies in the GameTree.
    """

    root_states: WorldState
    metadata: Dict[str, Any] = None

    def __post_init__(self) -> None:
        # TODO(discuss): How much do we want to limit what users can do here? For example, should we throw errors if stage != 0 on root node?
        # TODO(discuss): How should we allow folks to "load" a game tree?
        if self.metadata == None:
            # Define some metadata about the tree we want to keep updated+have easy access to throughout
            self.metadata = {}
            self.metadata["root_node"] = GameNode(
                stage=0,
                node_idx=0,
                parents=[],
                children=[],
                world_state=self.root_states,
                actions=None,
            )
            self.metadata["max_depth"] = (
                0  # Generally should match max stage of the current round #TODO(discuss): Should we rename? Depends how we engage with this thing
            )
            self.metadata["num_nodes"] = (
                1  # Monotonically grows with each node we add to the tree
            )
            self.leaf_nodes = (
                []
            )  # Tracks leaf/"terminal" nodes. In some games these may start appearing before the last stage of a round.

            # Start building tree from root node
            self.metadata[
                "root_node"
            ].set_as_root()  # Set as the root node (requires a special designation as None type else will be overwritten with empty list)
            self.__setitem__(
                str(self.metadata["root_node"].stage), [self.metadata["root_node"]]
            )

    @abc.abstractmethod
    def append_node_states(
        self,
        stage: int,
        node_idx: int,
        states: WorldState,
        pruning_functions: Dict[str, Callable | None],
    ) -> None:
        """
        Append states required for the agent to generate/make actions in a specific node
        """
        pass

    @abc.abstractmethod
    def append_node_actions(self, stage: int, node_idx: int, actions: Any) -> None:
        """
        Append output(s) from the agent's generation/rollout/decision/etc. relevant to a specific node
        """
        pass

    @abc.abstractmethod
    def commit_actions_from_stage(
        self, stage: int, tree_branching_functions: Dict[str, Callable | None]
    ) -> bool:
        """
        Create children for a specific node
        Created children should inherit relevant state information from parent's actions/states
        Also, should ensure parents and children are linked appropriately
        """
        pass

    # Optional methods. NOTE: Mainly useful GameTree "health checks"
    def all_branches_terminal(self) -> bool:
        """
        Traverses game tree and determines if all branches are terminal, i.e. tree will no longer grow this round.
        Return True if no active nodes can exist in the tree, else False.
        """
        pass

    def dedupe_node_list(self, node_list: List[GameNode]) -> bool:
        """
        Check whether there are duplicates of the same node in a list of nodes, e.g. the list of leaf_nodes or a stage's nodes
        """
        return node_list

    # Methods for emulating a mapping container object
    def __getitem__(self, key):
        try:
            return getattr(self, str(key))
        except:
            # TODO: Add warning here saying what the key is + exception that was raised that led to this.
            setattr(
                self, str(key), []
            )  # If attribute doesn't exist, then go ahead and set default value
            return getattr(self, str(key))

    def __setitem__(self, key, value):
        setattr(self, str(key), value)

    def __len__(
        self,
    ) -> (
        Dict
    ):  # TODO(discuss): Should we use something like this for easier info getting or just give depth for easier iterating on stages?
        return {
            "num_stages": self.metadata["max_depth"],
            "total_nodes": self.metadata["num_nodes"],
            "num_terminal_nodes": len(self.leaf_nodes),
        }


@dataclass
class DefaultGameTree(GameTree):
    """
    Default GameTree implementation with some basic functionality baked in.
    Assumes a fixed number of stages for each branch
    Assumes that parents/children cannot be from the same stage
    """

    def append_node_states(
        self,
        stage: int,
        node_idx: int,
        states: WorldState,
        pruning_functions: Dict[str, Callable | None],
    ) -> None:
        # Fetch relevant tree node
        node = self.__getitem__(stage)[node_idx]
        # Set environment states
        if pruning_functions["environment_pruner"] is not None:
            node.world_state.environment_states = pruning_functions[
                "environment_pruner"
            ](states.environment_states)
        else:
            node.world_state.environment_states = states.environment_states
        # Set opponent states
        if pruning_functions["opponent_pruner"] is not None:
            node.world_state.opponent_states = pruning_functions["opponent_pruner"](
                states.opponent_states
            )
        else:
            node.world_state.opponent_states = states.opponent_states
        # Set personal states
        if pruning_functions["personal_pruner"] is not None:
            node.world_state.personal_states = pruning_functions["personal_pruner"](
                states.personal_states
            )
        else:
            node.world_state.personal_states = states.personal_states

    def append_node_actions(self, stage: int, node_idx: int, actions: Any) -> None:
        # Fetch relevant tree node
        node = self.__getitem__(stage)[node_idx]
        # Set actions
        node["actions"] = actions

    def commit_actions_from_stage(
        self, stage: int, tree_branching_functions: Dict[str, Callable | None]
    ) -> None:
        # Get list of nodes from this stage
        stage_nodes = self.__getitem__(stage)

        # Determine if nodes should be considered terminal now that this stage of the tree is concluding
        if (
            tree_branching_functions["terminal_node_decision_function"] is not None
        ):  # Terminal decision fxn was provided
            terminal_nodes = tree_branching_functions[
                "terminal_node_decision_function"
            ](
                stage_nodes
            )  # Returns list of terminal nodes
            if terminal_nodes is None:
                terminal_nodes = []
            for node in terminal_nodes:
                node.set_as_terminal()
                self.leaf_nodes.append(node)

        stage += 1
        # Create children and determine node inheritance
        if (
            tree_branching_functions["stage_inheritance_function"] is not None
        ):  # Inheritance fxn was provided
            stage_children = tree_branching_functions["stage_inheritance_function"](
                stage_nodes
            )  # Returns list of lists containing children. Indexing on first list should be consistent with current stage nodes. Each list at said index corresponds to that node's children.
            assert len(stage_nodes) == len(
                stage_children
            ), f"Outermost list returned by the stage_inheritance_function should have the same length as the input list of nodes from the current stage! Length of outermost list returned was {len(stage_children)}, but length of input list was {len(stage_nodes)}."
            for i, node in enumerate(stage_nodes):
                if node._is_leaf_node():
                    pass
                else:
                    assert isinstance(
                        stage_children[i], List
                    ), "Each index of the outermost list returned by the stage_inheritance_function must be a list of children for the input node at this index! NOTE: If a node in the stage should not have children, please return an empty list at that index."
                    for child in stage_children[i]:
                        child.stage = stage
                        child.node_idx = len(self.__getitem__(stage))
                        _, _ = node.append_child(child), child.append_parent(node)
                        self.__getitem__(stage).append(child)
        else:  # No inferitance function provided, so will create child for each node in stage for all actions in rollout with states copied
            for node in stage_nodes:
                if node._is_leaf_node():
                    pass
                else:
                    for (
                        action
                    ) in (
                        node.actions
                    ):  # NOTE: Assumes rollout is wrapped in an iterable
                        child = GameNode(
                            stage=stage,
                            node_idx=len(self.__getitem__(stage)),
                            world_state=node.world_state,
                            actions=action,
                        )
                        _, _ = node.append_child(child), child.append_parent(node)
                        self.__getitem__(stage).append(child)
        self.metadata["num_nodes"] += len(self.__getitem__(stage))

        if not self.all_branches_terminal():
            self.metadata["max_depth"] = stage  # Increment max depth if needed

    # Optional methods
    def all_branches_terminal(
        self,
    ) -> bool:  # Default assumes all active nodes are in the current stage
        stage_nodes = self.__getitem__(self.metadata["max_depth"])
        nodes_are_terminal = [node._is_leaf_node() for node in stage_nodes]
        return all(nodes_are_terminal)

    def dedupe_node_list(self, node_list: List[GameNode]) -> bool:
        # TODO(Non-Urgent): Implement a default for this so people can use.
        return node_list
