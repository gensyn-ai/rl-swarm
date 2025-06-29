import logging
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from pythonjsonlogger import jsonlogger

# Add the parent directory to the Python path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Note: We're patching hivemind_exp functions (rewards_key, get_dht_value, get_name_from_peer_id)
# because these functions are only copied over at build time in Docker and aren't available during local testing.
# This allows us to test the DHTPublisher class without needing the actual hivemind_exp module.

from api.dht_pub import GossipDHTPublisher
from api.game_tree import Payload, WorldState, to_bytes, from_bytes
from api.kinesis import GossipMessage, GossipMessageData


# Wraps data put into the DHT so we can mock the DHT.get method
class DummyValue:
    def __init__(self, value):
        self.value = value


class TestGossipDHTPublisher:
    """Tests for the GossipDHTPublisher class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock objects
        self.mock_dht = MagicMock()
        self.mock_kinesis = MagicMock()

        # Create a real logger for testing
        self.mock_logger = logging.getLogger("test_logger")
        self.mock_logger.setLevel(logging.INFO)

        # Add a handler to the logger so caplog can capture the logs
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)

        # Use the JSON formatter from python-json-logger
        json_formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(message)s %(extra)s"
        )
        handler.setFormatter(json_formatter)
        self.mock_logger.addHandler(handler)

        self.coordinator = MagicMock()

        # Create the publisher with a short poll interval for testing
        self.publisher = GossipDHTPublisher(
            dht=self.mock_dht,
            kinesis_client=self.mock_kinesis,
            logger=self.mock_logger,
            poll_interval_seconds=0.1,
            coordinator=self.coordinator,
        )

    def teardown_method(self):
        """Clean up after tests."""
        # Stop the publisher if it's running
        if self.publisher.running:
            self.publisher.stop()
            # Give it a moment to stop
            time.sleep(0.2)

    def test_initialization(self, caplog):
        """Test that the publisher initializes correctly."""
        # Set the caplog level to capture INFO messages
        caplog.set_level(logging.INFO)

        # Re-initialize the publisher to capture the logs
        self.publisher = GossipDHTPublisher(
            dht=self.mock_dht,
            kinesis_client=self.mock_kinesis,
            logger=self.mock_logger,
            poll_interval_seconds=0.1,
            coordinator=self.coordinator,
        )

        # Verify the log message was captured
        assert len(caplog.records) > 0
        assert caplog.records[0].message == "GossipDHTPublisher initialized"

        # Verify other properties
        assert self.publisher.dht == self.mock_dht
        assert self.publisher.kinesis_client == self.mock_kinesis
        assert self.publisher.coordinator == self.coordinator
        assert self.publisher.poll_interval_seconds == 0.1
        assert self.publisher.current_round == -1
        assert self.publisher.current_stage == -1
        assert self.publisher.last_polled is None
        assert self.publisher.running is False
        assert self.publisher._poll_thread is None

    def test_poll_once_no_change(self, caplog):
        """Test polling when there's no round/stage change."""
        # Set up the coordinator mock to return the same round/stage
        self.coordinator.get_round_and_stage.return_value = (1, 1)
        self.publisher.current_round = 1
        self.publisher.current_stage = 1

        # Poll once
        self.publisher._poll_once()

        # Check that get_round_and_stage was called on the coordinator
        self.coordinator.get_round_and_stage.assert_called_once()

        # Check that the round/stage didn't change
        assert self.publisher.current_round == 1
        assert self.publisher.current_stage == 1

        # Check that the logger was called
        assert len(caplog.records) > 0
        assert caplog.records[0].message == "Polled for round/stage"
        assert caplog.records[0].round == 1
        assert caplog.records[0].stage == 1

        # Check that last_polled was updated
        assert self.publisher.last_polled is not None

    def test_poll_once_error(self, caplog):
        """Test polling when there's an error."""
        # Set up the coordinator mock to raise an exception
        self.coordinator.get_round_and_stage.side_effect = Exception("Test error")

        # Poll once
        self.publisher._poll_once()

        # Check that get_round_and_stage was called on the coordinator
        self.coordinator.get_round_and_stage.assert_called_once()

        # Check that the round/stage didn't change
        assert self.publisher.current_round == -1
        assert self.publisher.current_stage == -1

        # Check that the logger was called with the error
        assert len(caplog.records) > 0
        assert caplog.records[0].message == "Error polling for round/stage in gossip"
        assert caplog.records[0].error == "Test error"

        # Check that last_polled was not updated
        assert self.publisher.last_polled is None

    def test_publish_gossip(self, caplog):
        """Test publishing gossip data."""
        # Set up test data
        gossip_data = [
            (
                1000.0,
                {
                    "id": "id1",
                    "message": "message1",
                    "node": "node1",
                    "nodeId": "peer_id_1",
                    "dataset": "math",
                },
            ),
            (
                1001.0,
                {
                    "id": "id2",
                    "message": "message2",
                    "node": "node2",
                    "nodeId": "peer_id_2",
                },
            ),
        ]

        # Mock the Kinesis client's put_gossip method
        self.publisher.kinesis_client.put_gossip = MagicMock()

        # Publish gossip
        self.publisher._publish_gossip(gossip_data)

        # Check that put_gossip was called
        self.publisher.kinesis_client.put_gossip.assert_called_once()

        # Get the actual message that was passed to put_gossip
        actual_message = self.publisher.kinesis_client.put_gossip.call_args[0][0]

        # Check that the message has the correct type
        assert actual_message.type == "gossip"

        # Check that the message has the correct data
        assert len(actual_message.data) == 2

        # Check the first data item
        assert actual_message.data[0].id == "id1"
        assert actual_message.data[0].message == "message1"
        assert actual_message.data[0].peer_name == "node1"
        assert actual_message.data[0].peer_id == "peer_id_1"
        assert actual_message.data[0].dataset == "math"

        # Check the second data item
        assert actual_message.data[1].id == "id2"
        assert actual_message.data[1].message == "message2"
        assert actual_message.data[1].peer_name == "node2"
        assert actual_message.data[1].peer_id == "peer_id_2"
        assert actual_message.data[1].dataset is None

        # Check that the logger was called
        assert len(caplog.records) > 0
        assert caplog.records[0].message == "Publishing gossip messages"
        assert caplog.records[0].num_messages == 2

    def test_publish_gossip_no_data(self, caplog):
        """Test publishing gossip when there's no data."""
        # Mock the Kinesis client's put_gossip method
        self.publisher.kinesis_client.put_gossip = MagicMock()

        # Publish gossip with empty list
        self.publisher._publish_gossip([])

        # Check that put_gossip was not called
        assert self.publisher.kinesis_client.put_gossip.call_count == 0

        # Check that the logger was called
        assert len(caplog.records) > 0
        assert caplog.records[0].message == "No gossip data to publish"

    def test_poll_once_with_change(self, caplog):
        """Test publishing gossip with a real payload from the DHT."""
        # Create a test payload
        world_state = WorldState(
            environment_states={
                "question": "What is 2+2?",
                "metadata": {"source_dataset": "calendar_arithmetic"},
            },
            opponent_states=None,
            personal_states=None,
        )
        payload = Payload(world_state=world_state, actions=["4"], metadata=None)

        # Create the payload dictionary structure
        payload_dict = {"question_id": [payload]}

        # Create a mock value with expiration
        value_with_expiration = MagicMock()
        value_with_expiration.value = to_bytes(payload_dict)

        # Mock the DHT's get method to return a ValueWithExpiration
        self.publisher.dht.get = MagicMock(
            return_value=MagicMock(value={"test_peer_id": value_with_expiration})
        )

        # Mock the Kinesis client's put_gossip method
        self.publisher.kinesis_client.put_gossip = MagicMock()

        # Set up the coordinator mock to return a different round/stage
        self.coordinator.get_round_and_stage.return_value = (2, 1)
        self.publisher.current_round = 1
        self.publisher.current_stage = 1

        # Poll once
        self.publisher._poll_once()

        # Check that get_round_and_stage was called on the coordinator
        self.coordinator.get_round_and_stage.assert_called_once()

        # Check that the round/stage changed
        assert self.publisher.current_round == 2
        assert self.publisher.current_stage == 1

        # Check that _publish_gossip was called
        self.publisher.kinesis_client.put_gossip.assert_called_once()

        # Get the actual message that was passed to put_gossip
        actual_message = self.publisher.kinesis_client.put_gossip.call_args[0][0]

        # Check that the message has the correct type
        assert actual_message.type == "gossip"

        # Check that the message has the correct data
        assert len(actual_message.data) == 1

        # Check the data item
        data_item = actual_message.data[0]
        assert data_item.message == "What is 2+2?...4"
        assert data_item.peer_name == "solitary finicky meerkat"
        assert data_item.peer_id == "test_peer_id"
        assert data_item.dataset == "calendar_arithmetic"  # Should be from metadata
