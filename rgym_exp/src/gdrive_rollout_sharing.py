"""
Google Drive Rollout Sharing Module

Manages rollout publishing and fetching via Google Drive files.
Supports configurable publish frequency and retention policies.
"""

import json
import os
import shutil
import time
from typing import Any, Dict, List, Optional, Tuple

from rgym_exp.vendor.genrl.logging_utils.global_defs import get_logger


class GDriveRolloutSharing:
    """
    Manages rollout file operations on Google Drive.

    Supports:
    - Configurable publish frequency (generation/stage/round)
    - Configurable retention policy (keep all, keep N rounds, archive)
    - Local caching to reduce API calls
    - Retry logic for API rate limits
    """

    def __init__(
        self,
        gdrive_path: str,
        experiment_name: str,
        publish_frequency: str = 'stage',
        retention_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize rollout sharing.

        Args:
            gdrive_path: Base Google Drive path (e.g., /content/drive/MyDrive/rl-swarm)
            experiment_name: Name of experiment (e.g., qwen_0.6b_seed42)
            publish_frequency: When to publish - 'generation', 'stage', or 'round'
            retention_config: Cleanup/archive settings
        """
        self.gdrive_path = gdrive_path
        self.experiment_name = experiment_name
        self.publish_frequency = publish_frequency
        self.retention_config = retention_config or {'cleanup_enabled': False}

        # Paths
        self.rollouts_path = os.path.join(
            gdrive_path, 'experiments', experiment_name, 'rollouts'
        )
        self.archive_path = self.retention_config.get(
            'archive_path',
            os.path.join(gdrive_path, 'archives', experiment_name, 'rollouts')
        )

        # Create directories
        os.makedirs(self.rollouts_path, exist_ok=True)
        if self.retention_config.get('archive_old_rollouts', False):
            os.makedirs(self.archive_path, exist_ok=True)

        # Buffering for stage/round frequencies
        self._rollout_buffer = {}  # {(peer_id, round, stage): [rollouts_dicts]}

        get_logger().info(
            f"Initialized GDrive rollout sharing: "
            f"frequency={publish_frequency}, "
            f"cleanup={self.retention_config.get('cleanup_enabled', False)}"
        )

    def publish_rollouts(
        self,
        peer_id: str,
        round_num: int,
        stage: int,
        generation: int,
        rollouts_dict: Dict[int, List[Any]]
    ) -> bool:
        """
        Publish rollouts to Google Drive based on configured frequency.

        Args:
            peer_id: Node identifier
            round_num: Current round number
            stage: Current stage number
            generation: Current generation number
            rollouts_dict: {batch_id: [payloads]} from trainer

        Returns:
            True if published, False if buffered for later
        """
        if self.publish_frequency == 'generation':
            # Publish immediately
            self._write_rollouts_to_drive(peer_id, round_num, stage, rollouts_dict)
            return True

        elif self.publish_frequency == 'stage':
            # Buffer until stage ends
            buffer_key = (peer_id, round_num, stage)
            if buffer_key not in self._rollout_buffer:
                self._rollout_buffer[buffer_key] = []
            self._rollout_buffer[buffer_key].append(rollouts_dict)
            return False

        elif self.publish_frequency == 'round':
            # Buffer until round ends
            buffer_key = (peer_id, round_num)
            if buffer_key not in self._rollout_buffer:
                self._rollout_buffer[buffer_key] = []
            self._rollout_buffer[buffer_key].append(rollouts_dict)
            return False

        else:
            get_logger().error(f"Invalid publish_frequency: {self.publish_frequency}")
            return False

    def flush_buffer(
        self,
        peer_id: str,
        round_num: int,
        stage: Optional[int] = None
    ):
        """
        Flush buffered rollouts to Drive.

        Args:
            peer_id: Node identifier
            round_num: Round number
            stage: Stage number (for stage frequency, None for round frequency)
        """
        if self.publish_frequency == 'stage' and stage is not None:
            buffer_key = (peer_id, round_num, stage)
        elif self.publish_frequency == 'round':
            buffer_key = (peer_id, round_num)
        else:
            return

        if buffer_key not in self._rollout_buffer:
            return

        # Merge all buffered rollouts
        merged_rollouts = {}
        for rollouts_dict in self._rollout_buffer[buffer_key]:
            for batch_id, payloads in rollouts_dict.items():
                if batch_id not in merged_rollouts:
                    merged_rollouts[batch_id] = []
                merged_rollouts[batch_id].extend(payloads)

        # Write to Drive
        stage_to_write = stage if stage is not None else 0
        self._write_rollouts_to_drive(peer_id, round_num, stage_to_write, merged_rollouts)

        # Clear buffer
        del self._rollout_buffer[buffer_key]
        get_logger().debug(f"Flushed buffer for {buffer_key}")

    def _write_rollouts_to_drive(
        self,
        peer_id: str,
        round_num: int,
        stage: int,
        rollouts_dict: Dict[int, List[Any]]
    ):
        """
        Write rollouts to Google Drive with retry logic.

        Args:
            peer_id: Node identifier
            round_num: Round number
            stage: Stage number
            rollouts_dict: {batch_id: [payloads]}
        """
        # Create directory structure
        round_stage_path = os.path.join(
            self.rollouts_path,
            f'round_{round_num}',
            f'stage_{stage}'
        )
        os.makedirs(round_stage_path, exist_ok=True)

        # File path
        rollout_file = os.path.join(round_stage_path, f'{peer_id}.json')

        # Prepare data
        data = {
            'peer_id': peer_id,
            'round': round_num,
            'stage': stage,
            'timestamp': time.time(),
            'publish_frequency': self.publish_frequency,
            'rollouts': rollouts_dict
        }

        # Write with retry
        success = self._retry_with_backoff(
            lambda: self._write_json_file(rollout_file, data),
            max_retries=5
        )

        if success:
            get_logger().debug(
                f"Published rollouts: round={round_num}, stage={stage}, peer={peer_id}"
            )
        else:
            get_logger().error(f"Failed to publish rollouts after retries: {rollout_file}")

    def fetch_rollouts(
        self,
        round_num: int,
        stage: int,
        max_peers: int = 10,
        exclude_peer_ids: Optional[List[str]] = None,
        timeout_seconds: int = 30
    ) -> Dict[str, Dict[int, List[Any]]]:
        """
        Fetch rollouts from other peers.

        Args:
            round_num: Current round number
            stage: Current stage number
            max_peers: Maximum number of peers to fetch from
            exclude_peer_ids: Peers to exclude (e.g., self)
            timeout_seconds: Max time to wait for Drive operations

        Returns:
            {peer_id: {batch_id: [payloads]}} - same format as Hivemind
        """
        exclude_peer_ids = exclude_peer_ids or []
        rollouts = {}

        # Directory to fetch from
        round_stage_path = os.path.join(
            self.rollouts_path,
            f'round_{round_num}',
            f'stage_{stage}'
        )

        if not os.path.exists(round_stage_path):
            get_logger().debug(
                f"No rollouts directory for round={round_num}, stage={stage}"
            )
            return rollouts

        # List rollout files
        try:
            files = [
                f for f in os.listdir(round_stage_path)
                if f.endswith('.json')
            ]
        except OSError as e:
            get_logger().error(f"Failed to list rollout directory: {e}")
            return rollouts

        # Fetch from files
        start_time = time.time()
        for filename in files:
            if time.time() - start_time > timeout_seconds:
                get_logger().warning(f"Fetch timeout after {timeout_seconds}s")
                break

            if len(rollouts) >= max_peers:
                break

            # Extract peer_id from filename
            peer_id = filename.replace('.json', '')
            if peer_id in exclude_peer_ids:
                continue

            # Read file
            file_path = os.path.join(round_stage_path, filename)
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                # Validate format
                if 'rollouts' not in data:
                    get_logger().warning(f"Invalid rollout file format: {filename}")
                    continue

                rollouts[peer_id] = data['rollouts']
                get_logger().debug(f"Fetched rollouts from {peer_id}")

            except json.JSONDecodeError:
                get_logger().warning(f"Corrupted rollout file: {filename}")
                continue
            except Exception as e:
                get_logger().error(f"Error reading rollout file {filename}: {e}")
                continue

        get_logger().info(
            f"Fetched rollouts from {len(rollouts)} peers "
            f"for round={round_num}, stage={stage}"
        )
        return rollouts

    def cleanup_old_rollouts(self, current_round: int):
        """
        Clean up old rollouts based on retention policy.

        Args:
            current_round: Current round number
        """
        if not self.retention_config.get('cleanup_enabled', False):
            return

        keep_n = self.retention_config.get('keep_last_n_rounds', 5)
        archive = self.retention_config.get('archive_old_rollouts', False)

        cutoff_round = current_round - keep_n

        get_logger().info(
            f"Cleaning up rollouts older than round {cutoff_round} "
            f"(current={current_round}, keep_last_n={keep_n})"
        )

        # List round directories
        if not os.path.exists(self.rollouts_path):
            return

        try:
            round_dirs = [
                d for d in os.listdir(self.rollouts_path)
                if d.startswith('round_') and os.path.isdir(
                    os.path.join(self.rollouts_path, d)
                )
            ]
        except OSError as e:
            get_logger().error(f"Failed to list rollouts directory: {e}")
            return

        # Clean up old rounds
        cleaned = 0
        for round_dir in round_dirs:
            try:
                round_num = int(round_dir.replace('round_', ''))
            except ValueError:
                continue

            if round_num < cutoff_round:
                if archive:
                    self._archive_round(round_num)
                else:
                    self._delete_round(round_num)
                cleaned += 1

        if cleaned > 0:
            get_logger().info(
                f"Cleaned up {cleaned} old round(s) "
                f"({'archived' if archive else 'deleted'})"
            )

    def _archive_round(self, round_num: int):
        """
        Move rollouts from active dir to archive.

        Args:
            round_num: Round number to archive
        """
        source = os.path.join(self.rollouts_path, f'round_{round_num}')
        dest = os.path.join(self.archive_path, f'round_{round_num}')

        try:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.move(source, dest)
            get_logger().debug(f"Archived round {round_num}")
        except Exception as e:
            get_logger().error(
                f"Failed to archive round {round_num}: {e}, deleting instead"
            )
            self._delete_round(round_num)

    def _delete_round(self, round_num: int):
        """
        Permanently delete rollouts for a round.

        Args:
            round_num: Round number to delete
        """
        path = os.path.join(self.rollouts_path, f'round_{round_num}')

        try:
            if os.path.exists(path):
                shutil.rmtree(path)
                get_logger().debug(f"Deleted round {round_num}")
        except Exception as e:
            get_logger().error(f"Failed to delete round {round_num}: {e}")

    @staticmethod
    def _write_json_file(file_path: str, data: Dict[str, Any]):
        """
        Write JSON file atomically.

        Args:
            file_path: Path to file
            data: Data to write
        """
        # Write to temp file first
        temp_path = file_path + '.tmp'
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=2)

        # Atomic rename
        os.replace(temp_path, file_path)

    @staticmethod
    def _retry_with_backoff(func, max_retries: int = 5) -> bool:
        """
        Retry function with exponential backoff.

        Args:
            func: Function to retry
            max_retries: Maximum number of retries

        Returns:
            True if successful, False if all retries failed
        """
        for attempt in range(max_retries):
            try:
                func()
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    get_logger().warning(
                        f"Operation failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {wait}s..."
                    )
                    time.sleep(wait)
                else:
                    get_logger().error(
                        f"Operation failed after {max_retries} attempts: {e}"
                    )
                    return False
        return False
