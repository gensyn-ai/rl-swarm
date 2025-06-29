import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel, Field, field_serializer


class KinesisError(Exception):
    """Base exception for Kinesis operations"""

    pass


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class GossipMessageData(BaseModel):
    """Data for a single gossip message"""

    id: str
    peer_id: str = Field(..., alias="peerId")
    peer_name: str = Field(..., alias="peerName")
    dataset: Optional[str] = None
    message: str
    timestamp: datetime

    @field_serializer("timestamp")
    def serialize_timestamp(self, dt: datetime, _info):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        # Convert to UTC and format as RFC3339
        utc_dt = dt.astimezone(timezone.utc)
        # Format with 'Z' for UTC timezone (RFC3339)
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class GossipMessage(BaseModel):
    """Message type for gossip messages"""

    type: Literal["gossip"] = "gossip"
    data: List[GossipMessageData]


class Kinesis:
    def __init__(self, stream_name: str = ""):
        self.stream_name = stream_name
        self.logger = logging.getLogger(__name__)

        # If no stream name is provided, use no-op implementation
        if not stream_name:
            self.logger.info(
                "No Kinesis stream name provided, using no-op implementation"
            )
            self.kinesis = None
            return

        # Initialize Kinesis client if stream name is provided
        self.kinesis = boto3.client("kinesis", region_name="us-west-2")

        # Verify stream exists
        try:
            self.kinesis.describe_stream(StreamName=stream_name)
            self.logger.info(f"Successfully connected to Kinesis stream: {stream_name}")
        except ClientError as e:
            self.logger.error(
                f"Failed to connect to Kinesis stream {stream_name}: {str(e)}"
            )
            raise KinesisError(f"Stream {stream_name} not found or not accessible")

    def _put_record(self, data: Dict[str, Any], partition_key: str) -> None:
        """Put a record to Kinesis stream"""
        # No-op if no stream name was provided
        if not self.kinesis:
            self.logger.debug(
                f"No-op: received record {data} with partition key {partition_key}"
            )
            return

        try:
            self.logger.debug(
                f"Preparing to put record to Kinesis stream: {self.stream_name}"
            )
            self.logger.debug(f"Partition key: {partition_key}")
            self.logger.debug(f"Data: {json.dumps(data, cls=DateTimeEncoder)}")

            response = self.kinesis.put_record(
                StreamName=self.stream_name,
                Data=json.dumps(data, cls=DateTimeEncoder),
                PartitionKey=partition_key,
            )

            self.logger.info(
                f"Successfully put record to Kinesis stream: {self.stream_name}. "
                f"SequenceNumber: {response.get('SequenceNumber')}, "
                f"ShardId: {response.get('ShardId')}"
            )
        except ClientError as e:
            self.logger.error(
                f"Failed to put record to Kinesis: {str(e)}", exc_info=True
            )
            raise KinesisError(f"Failed to put record to Kinesis: {str(e)}")
        except Exception as e:
            self.logger.error(
                f"Unexpected error putting record to Kinesis: {str(e)}", exc_info=True
            )
            raise KinesisError(f"Unexpected error putting record to Kinesis: {str(e)}")

    def put_gossip(self, data: GossipMessage) -> None:
        """Put gossip data to Kinesis stream"""
        try:
            self.logger.info("Preparing to put gossip data to Kinesis")
            self.logger.debug(
                f"Gossip data: {json.dumps(data.model_dump(by_alias=True), cls=DateTimeEncoder)}"
            )
            self._put_record(data.model_dump(by_alias=True), "swarm-gossip")
            self.logger.info("Successfully put gossip data to Kinesis")
        except Exception as e:
            self.logger.error(f"Failed to put gossip data: {str(e)}", exc_info=True)
            raise KinesisError(f"Failed to put gossip data: {str(e)}")