import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

from .kinesis import (
    GossipMessage,
    GossipMessageData,
    Kinesis,
    KinesisError,
)

# Hardcoded UTC time for testing
TEST_TIME = datetime(2024, 3, 21, 12, 34, 56, 789000, tzinfo=timezone.utc)


@pytest.fixture
def mock_kinesis_client():
    """Create a mock Kinesis client"""
    with patch("boto3.client") as mock_client:
        # Create a mock client instance
        mock_kinesis = Mock()

        # Mock describe_stream response
        mock_kinesis.describe_stream.return_value = {
            "StreamDescription": {"StreamName": "test-stream", "StreamStatus": "ACTIVE"}
        }

        # Mock put_record response
        mock_kinesis.put_record.return_value = {
            "SequenceNumber": "1234567890",
            "ShardId": "shard-000000000001",
        }

        # Set the mock client to return our mock kinesis instance
        mock_client.return_value = mock_kinesis

        yield mock_kinesis


@pytest.fixture
def kinesis_instance(mock_kinesis_client):
    """Create a Kinesis instance with mocked client"""
    return Kinesis("test-stream")


def test_kinesis_initialization(mock_kinesis_client):
    """Test Kinesis client initialization"""
    kinesis = Kinesis("test-stream")
    assert kinesis.stream_name == "test-stream"
    mock_kinesis_client.describe_stream.assert_called_once_with(
        StreamName="test-stream"
    )


def test_kinesis_initialization_with_invalid_stream(mock_kinesis_client):
    """Test Kinesis client initialization with invalid stream"""
    mock_kinesis_client.describe_stream.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFoundException", "Message": "Stream not found"}},
        "DescribeStream",
    )

    with pytest.raises(
        KinesisError, match="Stream test-stream not found or not accessible"
    ):
        Kinesis("test-stream")


def test_put_gossip(kinesis_instance, mock_kinesis_client):
    """Test putting gossip data to Kinesis"""
    # Create test data with hardcoded time
    gossip_data = [
        GossipMessageData(
            id="msg1",
            peerId="peer1",
            peerName="Peer 1",
            message="Hello world",
            timestamp=TEST_TIME,
        )
    ]
    gossip_message = GossipMessage(data=gossip_data)

    # Call the method
    kinesis_instance.put_gossip(gossip_message)

    # Verify the client was called correctly
    mock_kinesis_client.put_record.assert_called_once()
    call_args = mock_kinesis_client.put_record.call_args[1]

    assert call_args["StreamName"] == "test-stream"
    assert call_args["PartitionKey"] == "swarm-gossip"

    # Verify the data was serialized correctly
    data = json.loads(call_args["Data"])
    assert data["type"] == "gossip"
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == "msg1"
    assert data["data"][0]["peerId"] == "peer1"
    assert data["data"][0]["message"] == "Hello world"
    # Timestamp should be in RFC3339 format with UTC
    assert data["data"][0]["timestamp"] == "2024-03-21T12:34:56.789000Z"


def test_kinesis_no_op_initialization():
    """Test Kinesis client initialization with no stream name (no-op mode)"""
    kinesis = Kinesis("")
    assert kinesis.stream_name == ""
    assert kinesis.kinesis is None


def test_kinesis_no_op_put_gossip(kinesis_instance, mock_kinesis_client):
    """Test putting gossip data in no-op mode"""
    # Create a no-op Kinesis instance
    no_op_kinesis = Kinesis("")

    # Create test data with hardcoded time
    gossip_data = [
        GossipMessageData(
            id="msg1",
            peerId="peer1",
            peerName="Peer 1",
            message="Hello world",
            timestamp=TEST_TIME,
        )
    ]
    gossip_message = GossipMessage(data=gossip_data)

    # Call the method - should not raise any errors
    no_op_kinesis.put_gossip(gossip_message)

    # Verify the client was not called
    mock_kinesis_client.put_record.assert_not_called()
