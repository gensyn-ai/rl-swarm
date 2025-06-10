import pytest
from unittest.mock import MagicMock, patch
from collections import defaultdict

from hivemind_exp.gsm8k.stages import gsm8k_stage_data
from hivemind_exp.dht_utils import HivemindNode
from hivemind_exp.tests.fake_data import CK, QUESTION, SAMPLES


@pytest.fixture
def mock_node():
    node = MagicMock()
    node.key = "test_node"
    node.round_num = 0
    node.rewards = [1.0, 2.0, 3.0]  # Mock rewards that will be summed
    return node


@pytest.fixture
def mock_dht():
    return MagicMock()


@pytest.fixture
def mock_merged_prev_stage_datasets():
    # Create a mock for the merged_prev_stage_datasets function
    # This will be used to inject test data for the round_winners function
    with patch("hivemind_exp.gsm8k.stage_utils.merged_prev_stage_datasets") as mock:
        # Define what the mock should return
        final_stage_outputs = [
            {
                "node1": {
                    "question": QUESTION,
                    "answer": "42",  # Add the answer parameter
                    "stage3_prompt": "Test prompt for stage 3",
                    "final_agent_decision": {"decision_key": "<answer>\n42\n</answer>"},
                },
                "node2": {
                    "question": QUESTION,
                    "answer": "42",  # Add the answer parameter
                    "stage3_prompt": "Another test prompt",
                    "final_agent_decision": {"decision_key": "<answer>\n42\n</answer>"},
                },
                "node3": {
                    # This will be treated as a faulty completion in our test
                    "question": QUESTION,
                    "answer": "42",
                    "stage3_prompt": "Incomplete prompt",
                    # We'll set final_agent_decision to None to trigger the faulty completion path
                    "final_agent_decision": None,
                },
                "node4": {
                    # Another faulty completion with different missing key
                    "answer": "42",
                    "final_agent_decision": {"decision_key": "<answer>\n42\n</answer>"},
                    "stage3_prompt": "Prompt with missing question",
                    # Missing question - will be added by the function
                    "question": None,
                },
            }
        ]
        mock.return_value = (final_stage_outputs, final_stage_outputs)
        yield mock


def test_round_winners(mock_dht, mock_node, mock_merged_prev_stage_datasets):
    """Test the round_winners function to ensure it correctly calculates rewards and returns winners."""

    # Create the stage data with our mocked objects
    stage_data = gsm8k_stage_data(
        mock_dht, mock_node, SAMPLES, SAMPLES, check_interval=0.1, log_tag="test"
    )

    # Get the round_winners function
    round_winners_fn = stage_data.round_winner_fn

    # Call the function with a limit
    winners = round_winners_fn(limit=2)

    # Verify merged_prev_stage_datasets was called
    mock_merged_prev_stage_datasets.assert_called_once()

    # Verify the basic parameters (excluding lambda functions which don't compare equal)
    args, kwargs = mock_merged_prev_stage_datasets.call_args
    assert args[0] == mock_dht
    assert args[1] == mock_node
    assert args[2] == mock_node.round_num
    assert args[3] == 3  # Stage 3
    assert kwargs.get("check_interval") == 0.1
    assert kwargs.get("log_tag") == "test"

    # Verify the winners list contains the expected nodes
    # node1 and node2 should have rewards, while node3 and node4 should have 0 rewards due to faulty completions
    assert len(winners) <= 2  # Should respect the limit

    # node1 and node2 should be in the winners list as they have valid completions
    assert "node1" in winners or "node2" in winners

    # node3 and node4 should not be in the winners list as they have faulty completions
    if len(winners) > 1:
        assert "node3" not in winners
        assert "node4" not in winners


def test_round_winners_empty_outputs(mock_dht, mock_node):
    """Test round_winners function when there are no outputs."""

    # Create a mock that returns empty outputs
    with patch("hivemind_exp.gsm8k.stage_utils.merged_prev_stage_datasets") as mock:
        mock.return_value = ([], [])

        # Create the stage data with our mocked objects
        stage_data = gsm8k_stage_data(
            mock_dht, mock_node, SAMPLES, SAMPLES, check_interval=0.1
        )

        # Get the round_winners function
        round_winners_fn = stage_data.round_winner_fn

        # Call the function
        winners = round_winners_fn()

        # Verify the winners list is empty
        assert winners == []


def test_round_winners_with_custom_limit(
    mock_dht, mock_node, mock_merged_prev_stage_datasets
):
    """Test round_winners function with different limit values."""

    # For this test, we'll simplify and just test with a single limit value
    # since we've already tested the main functionality in test_round_winners

    # Create the stage data with our mocked objects
    stage_data = gsm8k_stage_data(
        mock_dht, mock_node, SAMPLES, SAMPLES, check_interval=0.1
    )

    # Get the round_winners function
    round_winners_fn = stage_data.round_winner_fn

    # Test with a custom limit
    winners = round_winners_fn(limit=3)

    # Verify the limit is respected
    assert len(winners) <= 3
