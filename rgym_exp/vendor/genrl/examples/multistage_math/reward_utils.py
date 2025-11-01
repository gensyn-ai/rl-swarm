import re
from typing import Any, Dict, List

from rgym_exp.vendor.genrl.state import GameState


# General purpose reward fucntions
def format_reward(
    completions: List[str],
    pattern: str = r"\nAnswer: \d+",
    weight: float = 0.5,
    **kwargs,
) -> List[int]:
    matches = [re.search(pattern, content) for content in completions]
    return [weight if match else 0.0 for match in matches]


def correctness_reward(
    completions: List[str],
    correct: str,
    pattern: str = r"Answer: .*?([\d,]+(?:\.\d+)?)",
    weight: float = 1.0,
    **kwargs,
):
    rewards = []
    for completion in completions:
        try:
            match = re.search(pattern, completion)
            if match:
                answer = match.group(1)
                for remove_char in [",", "$", "%", "g"]:
                    answer = answer.replace(remove_char, "")
                if abs(float(answer) - float(correct)) < 1e-3:
                    rewards.append(weight)
                else:
                    rewards.append(0.0)
            else:
                rewards.append(0.0)
        except ValueError:
            rewards.append(0.0)
    return rewards


def validity_reward(
    completions: List[str],
    valid: List[str],
    pattern: str = r"Choice:.*?Student #([\d]+(?:\.\d+)?)",
    weight: float = 0.5,
    **kwargs,
):
    rewards = []
    for completion in completions:
        try:
            match = re.search(pattern, completion)
            if match:
                answer = match.group(1)
                if answer in valid:
                    rewards.append(weight)
                else:
                    rewards.append(0.0)
            else:
                rewards.append(0.0)
        except ValueError:
            rewards.append(0.0)
    return rewards


# Helper functions
def extract_responses(
    completion: str, pattern: str = r"Choice:.*?Student #([\d]+(?:\.\d+)?)"
):
    match = re.search(pattern, completion)
    if match:
        response = match.group(1)
        return response
    return "None"


# Game state parsers
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


def get_responses(game_state: GameState, stage: int) -> Dict[Any, Dict[Any, List[Any]]]:
    # Get responses being included as input to the current stage from the corresponding set of world-states
    world_states = game_state.get_stage_state(stage)
    responses = {}  # Key per agent
    for agent in world_states:
        responses[agent] = (
            {}
        )  # Will store an answer (or list of valid choices) per batch item
        for batch_id in world_states[agent]:
            responses[agent][batch_id] = []
            for node_idx, _ in enumerate(world_states[agent][batch_id]):
                responses[agent][batch_id].extend(
                    world_states[agent][batch_id][node_idx].opponent_states
                )
    return responses  # Indices are [Agent][Batch Item][Node Idx]


def parse_game_state(game_state, stage):
    if stage == 0:
        return get_completions(game_state, stage), get_answers(game_state, stage)
    elif stage == 1:
        return get_completions(game_state, stage), get_responses(game_state, stage)
    elif stage == 2:
        return get_completions(game_state, stage), get_answers(game_state, stage)
