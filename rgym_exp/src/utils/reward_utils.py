import re
from typing import Any, Dict, List, Optional

from genrl.state import GameState
from reasoning_gym.factory import get_score_answer_fn
from reasoning_gym.utils import compute_decimal_reward, extract_answer


def score_answer(
    predicted_answer: str, oracle_answer: str, metadata: Optional[Dict[str, Any]] = None
) -> float:
    """Score an answer using the dataset's scoring function if available."""
    if metadata and "source_dataset" in metadata:
        # Try to get the original dataset for scoring
        source_dataset = metadata["source_dataset"]
        scorer = get_score_answer_fn(source_dataset)
        entry = {"answer": oracle_answer, "metadata": metadata}
        return scorer(predicted_answer, entry)
    # Default to decimal reward computation from reasoning_gym.utils
    return compute_decimal_reward(predicted_answer, oracle_answer)


def format_reward(completions, weight=1.0):
    regex = r"^<think>([^<]*(?:<(?!/?think>)[^<]*)*)<\/think>\n<answer>([\s\S]*?)<\/answer>$"
    matches = [
        re.match(regex, completion, flags=re.DOTALL) for completion in completions
    ]
    return [weight if match else 0.0 for match in matches]


def accuracy_reward(completions, ground_truth, metadata, weight=1.0):
    predictions = [extract_answer(completion) for completion in completions]
    return [
        weight * score_answer(pred, ground_truth, metadata=metadata)
        for pred in predictions
    ]


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
                metadata[agent][batch_id].append(
                    world_states[agent][batch_id][node].environment_states["metadata"]
                )
    return metadata  # Indices are [Agent][Batch Item][Node Idx]


def parse_game_state(game_state, stage):
    return (
        get_completions(game_state, stage),
        get_answers(game_state, stage),
        get_metadata(game_state, stage),
    )
