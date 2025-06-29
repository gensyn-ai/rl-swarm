import hashlib
import logging
import threading
import time
import uuid
import random
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional
from .game_tree import Payload, from_bytes

from hivemind.dht import DHT

from hivemind_exp.chain_utils import ModalSwarmCoordinator
from hivemind_exp.dht_utils import get_dht_value, outputs_key, rewards_key
from hivemind_exp.name_utils import get_name_from_peer_id

from .kinesis import (
    GossipMessage,
    GossipMessageData,
    Kinesis,
)


class BaseDHTPublisher(ABC):
    """
    Base class for DHT publishers that poll the DHT for changes and publish data to Kinesis.
    This is an abstract base class that cannot be instantiated directly.
    """

    def __init__(
        self,
        dht: DHT,
        kinesis_client: Kinesis,
        logger: logging.Logger,
        poll_interval_seconds: int = 300,  # 5 minutes default
        coordinator: Optional[ModalSwarmCoordinator] = None,
    ):
        """
        Initialize the DHT publisher.

        Args:
            dht: The DHT instance to poll
            kinesis_client: The Kinesis client to publish to
            logger: Logger instance
            poll_interval_seconds: How often to poll the DHT (in seconds)
            coordinator: The coordinator to get round and stage information from
        """
        self.dht = dht
        self.kinesis_client = kinesis_client
        self.logger = logger
        self.poll_interval_seconds = poll_interval_seconds
        self.coordinator = coordinator

        # Thread control
        self._stop_event = threading.Event()
        self._poll_thread = None
        self.running = False

        # State tracking
        self.current_round = -1
        self.current_stage = -1
        self.last_polled = None
        self.poll_id = None

        # Store the class name for use in logging
        self.class_name = self.__class__.__name__

        self.logger.info(f"{self.class_name} initialized")

    def start(self):
        """Start the polling thread."""
        if self._poll_thread:
            self.logger.warning(f"{self.class_name} is already running")
            return

        self.logger.info(f"{self.class_name} starting")

        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()
        self.running = True
        self.logger.info(f"{self.class_name} started")

    def stop(self):
        """Stop the polling thread."""
        if not self._poll_thread:
            self.logger.warning(f"{self.class_name} is not running")
            return

        self._stop_event.set()
        self._poll_thread.join(timeout=5)
        self.running = False
        self.logger.info(f"{self.class_name} stopped")

    def get_last_polled(self):
        """Get the time of the last poll."""
        return self.last_polled

    def _get_rewards_data(
        self, round_num: int, stage_num: int
    ) -> dict[str, Any] | None:
        rewards_key_str = rewards_key(round_num, stage_num)
        rewards_data = get_dht_value(self.dht, key=rewards_key_str, beam_size=500)
        return rewards_data

    def _get_outputs_data(
        self, node_key: str, round_num: int, stage_num: int
    ) -> dict[str, Any] | None:
        outputs_key_str = outputs_key(node_key, round_num, stage_num)
        outputs_data = get_dht_value(self.dht, key=outputs_key_str)
        return outputs_data

    def _get_peer_name_from_id(self, peer_id: str) -> str:
        return get_name_from_peer_id(peer_id) or peer_id

    def _poll_loop(self):
        """Main polling loop."""

        while not self._stop_event.is_set():
            self.poll_id = str(uuid.uuid4())

            self.logger.info(
                "Polling for round/stage",
                extra={
                    "class": self.class_name,
                    "round": self.current_round,
                    "stage": self.current_stage,
                    "poll_id": self.poll_id,
                },
            )
            self._poll_once()
            time.sleep(self.poll_interval_seconds)

    @abstractmethod
    def _poll_once(self):
        """
        Perform a single poll of the DHT.
        This method should be overridden by subclasses to implement specific polling logic.
        """
        pass


class GossipDHTPublisher(BaseDHTPublisher):
    """
    A class that polls the DHT for gossip data and publishes it to Kinesis.
    """

    def __init__(
        self,
        dht: DHT,
        kinesis_client,
        logger=None,
        poll_interval_seconds: int = 300,
        coordinator=None,
    ):
        """Initialize the publisher."""
        super().__init__(
            dht, kinesis_client, logger, poll_interval_seconds, coordinator=coordinator
        )

    def _poll_once(self):
        try:
            new_round, new_stage = self.coordinator.get_round_and_stage()

            self.logger.info(
                "Polled for round/stage",
                extra={
                    "class": self.class_name,
                    "round": new_round,
                    "stage": new_stage,
                    "poll_id": self.poll_id,
                }
            )

            if new_round != self.current_round or new_stage != self.current_stage:
                self.logger.info(
                    "Round/stage changed",
                    extra={
                        "class": self.class_name,
                        "old_round": self.current_round,
                        "old_stage": self.current_stage,
                        "new_round": new_round,
                        "new_stage": new_stage,
                        "poll_id": self.poll_id,
                    }
                )

            # Update current round and stage
            self.current_round = new_round
            self.current_stage = new_stage

            round_gossip = []

            round_data = self.dht.get(str(self.current_round))
            if not round_data:
                self.logger.info("No gossip found for round", extra={"round": self.current_round})
                return

            # Update the last polled time
            self.last_polled = datetime.now(timezone.utc)

            for peer_id, value_with_expiration in round_data.value.items():
                bytes = value_with_expiration.value
                payload_dict = from_bytes(bytes)

                # Flatten the payloads into a list of payloads.
                all_payloads = []
                for _, payload_list in payload_dict.items():
                    all_payloads.extend(payload_list)

                # For each payload, generate a gossip message.
                for payload in all_payloads:
                    world_state_tuple = payload.world_state
                    question = world_state_tuple.environment_states["question"]
                    actions = payload.actions
                    source_dataset = world_state_tuple.environment_states["metadata"]["source_dataset"]
                    action = random.choice(actions) if actions else ""

                    # Stamp the message with the current time.
                    now_utc = datetime.now(timezone.utc)
                    ts = int(now_utc.timestamp())

                    # Generate a unique ID for the gossip message.
                    gossip_id = hashlib.md5(f"{question}-{peer_id}-{self.current_round}-{action}-{source_dataset}".encode()).hexdigest()
                    round_gossip.append((
                        ts, {
                            "id": gossip_id,
                            "message": f"{question}...{action}",
                            "node": get_name_from_peer_id(peer_id),
                            "nodeId": peer_id,
                            "dataset": source_dataset,
                        }
                    ))

            self.logger.info("Got gossip messages", extra={
                "message_count": len(round_gossip),
            })

            # Shuffle the gossip messages to attempt to avoid getting only 1 peer, and only publish 200.
            random.shuffle(round_gossip)
            round_gossip = round_gossip[:200]

            self._publish_gossip(round_gossip)

        except Exception as e:
            self.logger.error(
                "Error polling for round/stage in gossip",
                extra={
                    "class": self.class_name,
                    "error": str(e),
                    "poll_id": self.poll_id,
                },
            )

    def _publish_gossip(self, gossip: list[tuple[float, dict[str, Any]]]):
        """
        Publish gossip data to Kinesis.

        Args:
            gossip_data: The gossip data from the DHT
        """
        try:
            if not gossip:
                self.logger.info("No gossip data to publish")
                return

            self.logger.info(
                "Publishing gossip messages", extra={"num_messages": len(gossip)}
            )
            gossip_data = []

            for ts, g in gossip:
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                gossip_data.append(
                    GossipMessageData(
                        id=g["id"],
                        peerId=g["nodeId"],
                        peerName=g["node"],
                        message=g["message"],
                        timestamp=dt,
                        dataset=g.get("dataset"),
                    )
                )

            if len(gossip_data) > 0:
                self.kinesis_client.put_gossip(
                    GossipMessage(type="gossip", data=gossip_data)
                )
                self.logger.info("Successfully published gossip")

        except Exception as e:
            self.logger.error(
                "Error publishing gossip",
                extra={"error": str(e), "poll_id": self.poll_id},
            )
