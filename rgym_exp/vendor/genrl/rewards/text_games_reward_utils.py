import re
from typing import Any, Callable, Dict, List, Tuple

from rgym_exp.vendor.genrl.rewards.reward_manager import DefaultRewardManager
from rgym_exp.vendor.genrl.rewards.reward_store import RewardFnStore, RoundRewardFnStore
from rgym_exp.vendor.genrl.state import GameState


# General purpose reward fucntions
def calculate_reward(
    completions: List[str],  # List of completions,
    correct_answers: List[str],  # List of correct answers
    reward_conditions: List[Tuple[Callable[[str, str], bool], float]],
) -> List[float]:
    rewards = []
    for completion, correct in zip(completions, correct_answers):
        total_reward = sum(
            weight
            for reward_func, weight in reward_conditions
            if reward_func(completion, correct)
        )
        rewards.append(float(total_reward))
    return rewards


def format_reward_condition(
    pattern: str = r"\nAnswer: \d+", weight: float = 0.5
) -> Tuple[Callable[[str], bool], float]:
    regex = re.compile(pattern)
    reward_func = lambda s, _: bool(regex.search(s))
    return reward_func, weight


def correctness_reward_condition(
    tolerance: float = 1e-3,
    pattern: str = r"Answer: .*?([\d,]+(?:\.\d+)?)",
    weight: float = 1.0,
) -> Callable[[str, str], bool]:

    regex = re.compile(pattern)

    def condition(completion: str, correct: str) -> bool:
        try:
            match = regex.search(completion)
            if match:
                answer = match.group(1)
                for remove_char in [",", "$", "%", "g"]:
                    answer = answer.replace(remove_char, "")
                return abs(float(answer) - float(correct)) < tolerance
            else:
                return False
        except ValueError:
            return False

    return condition, weight


def get_completions(
    game_state: GameState, stage: int
) -> Dict[Any, Dict[Any, List[Any]]]:
    # Get completions per agent and batch item from corresponding set of actions
    actions = game_state.get_stage_actions(stage)
    completions = {}  # Key per agent
    for agent in actions:
        completions[agent] = {}  # Will store a list per batch item
        for batch_id in actions[agent]:
            completions[agent][
                batch_id
            ] = (
                []
            )  # Will store all completion strings for this batch item for this agent
            for node, _ in enumerate(actions[agent][batch_id]):
                completions[agent][batch_id].append(actions[agent][batch_id][node])
    return completions  # Indices are [Agent][Batch Item][Node Idx][Completion]


def get_answers(game_state: GameState, stage: int) -> Dict[Any, Dict[Any, List[Any]]]:
    # Get answers per agent and batch item from corresponding set of world-states
    world_states = game_state.get_stage_state(stage)
    answers = {}  # Key per agent
    for agent in world_states:
        answers[agent] = (
            {}
        )  # Will store an answer (or list of valid choices) per batch item
        for batch_id in world_states[agent]:
            answers[agent][batch_id] = []
            for node, _ in enumerate(world_states[agent][batch_id]):
                answers[agent][batch_id].append(
                    world_states[agent][batch_id][node].environment_states["answer"]
                )
    return answers  # Indices are [Agent][Batch Item][Node Idx]


def get_metadata(game_state: GameState, stage: int) -> Dict[Any, Dict[Any, List[Any]]]:
    # Get metadata per agent and batch item from corresponding set of world-states
    world_states = game_state.get_stage_state(stage)
    metadata = {}  # Key per agent
    for agent in world_states:
        metadata[agent] = (
            {}
        )  # Will store an answer (or list of valid choices) per batch item
        for batch_id in world_states[agent]:
            metadata[agent][batch_id] = []
            for node, _ in enumerate(world_states[agent][batch_id]):
                metadata[agent][batch_id].append("None")
    return metadata  # Indices are [Agent][Batch Item][Node Idx]


def parse_game_state(game_state, stage):
    return (
        get_completions(game_state, stage),
        get_answers(game_state, stage),
        get_metadata(game_state, stage),
    )


def get_default_reward_manager(reward_conditions, max_rounds=5):
    return DefaultRewardManager(
        reward_fn_store=RewardFnStore(
            max_rounds=max_rounds,
            reward_fn_stores=[
                RoundRewardFnStore(
                    num_stages=1,
                    reward_fns=[
                        RewardsWithConditions(reward_conditions=reward_conditions)
                    ],
                )
            ],
        )
    )


class RewardsWithConditions:
    def __init__(self, reward_conditions):
        self.reward_conditions = reward_conditions
        self.stage = 0
        self.reward_fn = self.cumulative_reward

    def cumulative_reward(self, completions, answer, metadata):
        if completions is None or not completions or not isinstance(completions, list):
            return [0.0]
        if answer is None or not answer:
            return [0.0] * len(completions)
        correct_answers = [answer] * len(completions)
        return calculate_reward(completions, correct_answers, self.reward_conditions)

    def __call__(self, game_state):
        completions, answers, metadata = parse_game_state(game_state, self.stage)
        rewards = {}  # Key per agent
        for agent in completions:
            rewards[agent] = {}  # Will store a list per batch item
            for batch_id in completions[agent]:
                rewards[agent][batch_id] = []
                for node_idx, _ in enumerate(completions[agent][batch_id]):
                    rewards[agent][batch_id].append(
                        self.reward_fn(
                            completions[agent][batch_id][node_idx],
                            answers[agent][batch_id][node_idx],
                            metadata[agent][batch_id][node_idx],
                        )
                    )
        return rewards
