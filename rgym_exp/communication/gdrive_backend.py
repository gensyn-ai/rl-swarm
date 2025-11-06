"""
Google Drive Communication Backend

GenRL-compatible communication backend that uses Google Drive for rollout sharing.
Replaces HivemindBackend with file-based approach.
"""

from typing import Any, Dict, List, Optional

from rgym_exp.vendor.genrl.communication.communication import Communication
from rgym_exp.vendor.genrl.logging_utils.global_defs import get_logger

from rgym_exp.src.gdrive_rollout_sharing import GDriveRolloutSharing


class GDriveCommunicationBackend(Communication):
    """
    Communication backend that uses Google Drive for rollout sharing.

    Implements the same interface as HivemindBackend but uses file-based
    rollout sharing via Google Drive instead of P2P DHT.
    """

    def __init__(
        self,
        gdrive_rollout_sharing: GDriveRolloutSharing,
        node_id: str,
        experiment_name: str,
        rollout_publish_frequency: str = 'stage',
        fetch_max_peers: int = 10,
        fetch_timeout_seconds: int = 30,
        cache_rollouts: bool = True,
        **kwargs
    ):
        """
        Initialize GDrive communication backend.

        Args:
            gdrive_rollout_sharing: Instance of GDriveRolloutSharing
            node_id: Unique node identifier (UUID, no crypto needed)
            experiment_name: Name of current experiment
            rollout_publish_frequency: 'generation', 'stage', or 'round'
            fetch_max_peers: Max peers to fetch rollouts from
            fetch_timeout_seconds: Timeout for Drive API
            cache_rollouts: Enable local caching
        """
        super().__init__()
        self.rollout_sharing = gdrive_rollout_sharing
        self.node_id = node_id
        self.experiment_name = experiment_name
        self.publish_frequency = rollout_publish_frequency
        self.fetch_max_peers = fetch_max_peers
        self.fetch_timeout = fetch_timeout_seconds

        self.current_round = 0
        self.current_stage = 0
        self.current_generation = 0

        # Local cache: {(round, stage): {peer_id: rollouts}}
        self.cache_enabled = cache_rollouts
        self.rollout_cache = {}

        get_logger().info(
            f"Initialized GDrive communication backend: "
            f"node_id={node_id}, frequency={rollout_publish_frequency}"
        )

    def get_id(self) -> str:
        """Return node identifier."""
        return self.node_id

    @property
    def step_(self) -> int:
        """Get current step (round number)."""
        return self.current_round

    @step_.setter
    def step_(self, value: int):
        """
        Set current step (round number).
        Triggers cache invalidation if round changed.
        """
        if value != self.current_round:
            old_round = self.current_round
            self.current_round = value
            if old_round > 0:  # Don't log on initialization
                get_logger().debug(f"Round advanced: {old_round} -> {value}")
            self._invalidate_cache()

    def publish_state(
        self,
        state_dict: Dict[Any, Any],
        stage: Optional[int] = None,
        generation: Optional[int] = None
    ):
        """
        Publish local rollouts to Google Drive.

        Args:
            state_dict: Contains rollouts in format {batch_id: [payloads]}
            stage: Current stage number (optional, uses self.current_stage if None)
            generation: Current generation (optional, uses self.current_generation if None)

        Behavior depends on rollout_publish_frequency:
            - 'generation': Publishes immediately
            - 'stage': Buffers until end of stage
            - 'round': Buffers until end of round
        """
        stage = stage if stage is not None else self.current_stage
        generation = generation if generation is not None else self.current_generation

        published = self.rollout_sharing.publish_rollouts(
            peer_id=self.node_id,
            round_num=self.current_round,
            stage=stage,
            generation=generation,
            rollouts_dict=state_dict
        )

        if published:
            get_logger().debug(
                f"Published rollouts: round={self.current_round}, "
                f"stage={stage}, generation={generation}"
            )
        else:
            get_logger().debug(
                f"Buffered rollouts (will publish at end of {self.publish_frequency})"
            )

    def get_swarm_states(
        self,
        round_num: Optional[int] = None,
        stage: Optional[int] = None
    ) -> Dict[str, Dict[int, List[Any]]]:
        """
        Fetch rollouts from all peers via Google Drive.

        Args:
            round_num: Round to fetch (uses self.current_round if None)
            stage: Stage to fetch (uses self.current_stage if None)

        Returns:
            {peer_id: {batch_id: [payloads]}} - same format as Hivemind

        Uses local cache to minimize Drive API calls.
        """
        round_num = round_num if round_num is not None else self.current_round
        stage = stage if stage is not None else self.current_stage

        cache_key = (round_num, stage)

        # Check cache first
        if self.cache_enabled and cache_key in self.rollout_cache:
            get_logger().debug(f"Using cached rollouts for round={round_num}, stage={stage}")
            return self.rollout_cache[cache_key]

        # Fetch from Drive
        get_logger().debug(
            f"Fetching rollouts from Drive: round={round_num}, stage={stage}"
        )

        swarm_states = self.rollout_sharing.fetch_rollouts(
            round_num=round_num,
            stage=stage,
            max_peers=self.fetch_max_peers,
            exclude_peer_ids=[self.node_id],
            timeout_seconds=self.fetch_timeout
        )

        # Cache the result
        if self.cache_enabled:
            self.rollout_cache[cache_key] = swarm_states
            get_logger().debug(f"Cached rollouts for {cache_key}")

        if swarm_states:
            get_logger().info(
                f"Fetched rollouts from {len(swarm_states)} peers "
                f"(round={round_num}, stage={stage})"
            )
        else:
            get_logger().debug(
                f"No external rollouts available for round={round_num}, stage={stage}"
            )

        return swarm_states

    def advance_generation(self):
        """Notify backend that generation has advanced."""
        self.current_generation += 1
        get_logger().debug(f"Generation advanced to {self.current_generation}")

    def advance_stage(self):
        """Notify backend that stage has advanced."""
        old_stage = self.current_stage

        # Flush buffered rollouts if frequency='stage'
        # Note: Only flush if we've completed at least one stage (stage 0+)
        if self.publish_frequency == 'stage' and self.current_stage >= 0:
            self.rollout_sharing.flush_buffer(
                self.node_id,
                self.current_round,
                old_stage
            )

        self.current_stage += 1
        self.current_generation = 0
        get_logger().debug(f"Stage advanced: {old_stage} -> {self.current_stage}")

    def advance_round(self):
        """Notify backend that round has advanced."""
        old_round = self.current_round
        old_stage = self.current_stage

        # Flush buffered rollouts based on frequency
        if old_round >= 0:
            if self.publish_frequency == 'round':
                self.rollout_sharing.flush_buffer(
                    self.node_id,
                    old_round
                )
            elif self.publish_frequency == 'stage':
                # Flush the completed stage before advancing round
                self.rollout_sharing.flush_buffer(
                    self.node_id,
                    old_round,
                    old_stage
                )

        self.current_round += 1
        self.current_stage = 0
        self.current_generation = 0

        # Trigger cleanup based on retention policy
        self.rollout_sharing.cleanup_old_rollouts(self.current_round)

        # Invalidate cache
        self._invalidate_cache()

        get_logger().debug(f"Round advanced: {old_round} -> {self.current_round}")

    def _invalidate_cache(self):
        """Clear cached rollouts when round advances."""
        if self.cache_enabled and self.rollout_cache:
            old_size = len(self.rollout_cache)
            self.rollout_cache.clear()
            get_logger().debug(f"Invalidated rollout cache ({old_size} entries)")

    # Compatibility methods for Communication base class
    def all_gather_object(self, obj: Any) -> Dict[str | int, Any]:
        """
        Gather objects from all peers.

        In GDrive mode, we publish local rollouts to GDrive and return local object.
        The actual gathering/fetching happens separately in data manager.

        Args:
            obj: Object to gather (communication payload dict: {batch_id: [Payload, ...]})

        Returns:
            Dict containing just this node's object (compatible with Communication interface)
        """
        # Publish local rollouts to GDrive (will buffer based on publish_frequency)
        if obj:  # Only publish if we have data
            get_logger().debug(
                f"Publishing rollouts via all_gather_object: "
                f"round={self.current_round}, stage={self.current_stage}"
            )
            self.publish_state(
                state_dict=obj,
                stage=self.current_stage,
                generation=self.current_generation
            )
        else:
            get_logger().debug("all_gather_object called with empty object, skipping publish")

        # Return dict with node_id as key (compatible with base Communication class)
        return {self.node_id: obj}

    @property
    def dht(self):
        """Return mock DHT object for compatibility with existing code."""
        return MockDHT()


class MockDHT:
    """
    Mock DHT object to maintain compatibility with existing code that
    expects HivemindBackend's DHT interface.
    """

    def get_visible_maddrs(self, latest: bool = True) -> List[str]:
        """
        Mock method for compatibility.

        In GDrive mode, there are no multiaddrs since we don't use P2P.

        Args:
            latest: Ignored

        Returns:
            Empty list (no multiaddrs in GDrive mode)
        """
        return []
