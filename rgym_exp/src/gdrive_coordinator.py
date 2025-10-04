"""
Google Drive-based Coordinator for RL Swarm

This module provides a file-based coordinator that uses Google Drive for state management,
replacing the blockchain-based coordinator. It implements the same interface as SwarmCoordinator
for compatibility with the existing codebase.
"""

import json
import os
import time
from typing import List, Tuple, Optional
from genrl.logging_utils.global_defs import get_logger


class GDriveSwarmCoordinator:
    """
    File-based coordinator that uses Google Drive for state management.
    Implements same interface as SwarmCoordinator for compatibility.
    """

    def __init__(self, gdrive_path: str, node_role: str = 'worker', round_check_interval: int = 30):
        """
        Initialize Google Drive coordinator.

        Args:
            gdrive_path: Base path in Google Drive (e.g., /content/drive/MyDrive/rl-swarm/experiments/exp1)
            node_role: 'coordinator' or 'worker'
            round_check_interval: Seconds between state checks
        """
        self.gdrive_path = gdrive_path
        self.node_role = node_role
        self.round_check_interval = round_check_interval

        # Initialize directory structure
        self._init_directories()

        get_logger().info(f"Initialized GDrive coordinator at {gdrive_path} as {node_role}")

    def _init_directories(self):
        """Create necessary directories in Google Drive"""
        dirs = ['state', 'peers', 'rewards', 'winners', 'checkpoints', 'logs']
        for d in dirs:
            dir_path = os.path.join(self.gdrive_path, d)
            os.makedirs(dir_path, exist_ok=True)

        # Initialize state file if coordinator and doesn't exist
        if self.node_role == 'coordinator':
            state_file = os.path.join(self.gdrive_path, 'state', 'current_state.json')
            if not os.path.exists(state_file):
                initial_state = {
                    "round": 0,
                    "stage": 0,
                    "created_at": time.time(),
                    "updated_at": time.time()
                }
                self._write_json_with_retry(state_file, initial_state)
                get_logger().info(f"Initialized state file at {state_file}")

    def register_peer(self, peer_id: str):
        """
        Register peer to Google Drive.

        Args:
            peer_id: Unique peer identifier
        """
        peer_file = os.path.join(self.gdrive_path, 'peers', f'{peer_id}.json')
        data = {
            "peer_id": peer_id,
            "registered_at": time.time(),
            "node_role": self.node_role
        }
        self._write_json_with_retry(peer_file, data)
        get_logger().info(f"Registered peer {peer_id} to Google Drive")

    def get_round_and_stage(self) -> Tuple[int, int]:
        """
        Read current round and stage from Google Drive state file.

        Returns:
            Tuple of (round_number, stage_number)
        """
        state_file = os.path.join(self.gdrive_path, 'state', 'current_state.json')
        state = self._read_json_with_retry(state_file)

        round_num = state.get('round', 0)
        stage_num = state.get('stage', 0)

        return round_num, stage_num

    def submit_reward(self, round_num: int, stage_num: int, reward: int, peer_id: str):
        """
        Submit reward to Google Drive.

        Args:
            round_num: Round number
            stage_num: Stage number
            reward: Reward value
            peer_id: Peer identifier
        """
        reward_dir = os.path.join(self.gdrive_path, 'rewards', f'round_{round_num}', f'stage_{stage_num}')
        os.makedirs(reward_dir, exist_ok=True)

        reward_file = os.path.join(reward_dir, f'{peer_id}.json')
        data = {
            "round": round_num,
            "stage": stage_num,
            "reward": reward,
            "peer_id": peer_id,
            "submitted_at": time.time()
        }
        self._write_json_with_retry(reward_file, data)
        get_logger().debug(f"Submitted reward for round {round_num}, stage {stage_num}")

    def submit_winners(self, round_num: int, winners: List[str], peer_id: str):
        """
        Submit winner votes to Google Drive.

        Args:
            round_num: Round number
            winners: List of winner peer IDs
            peer_id: Voting peer identifier
        """
        winner_dir = os.path.join(self.gdrive_path, 'winners', f'round_{round_num}')
        os.makedirs(winner_dir, exist_ok=True)

        winner_file = os.path.join(winner_dir, f'{peer_id}.json')
        data = {
            "round": round_num,
            "winners": winners,
            "peer_id": peer_id,
            "submitted_at": time.time()
        }
        self._write_json_with_retry(winner_file, data)
        get_logger().debug(f"Submitted winners for round {round_num}")

    def update_round_stage(self, new_round: int, new_stage: int):
        """
        Update global round/stage (coordinator only).
        Uses atomic write with temp file + rename.

        Args:
            new_round: New round number
            new_stage: New stage number

        Raises:
            ValueError: If called by non-coordinator node
        """
        if self.node_role != 'coordinator':
            raise ValueError("Only coordinator can update round/stage")

        state_file = os.path.join(self.gdrive_path, 'state', 'current_state.json')
        temp_file = f"{state_file}.tmp"

        data = {
            "round": new_round,
            "stage": new_stage,
            "updated_at": time.time(),
            "updated_by": "coordinator"
        }

        # Atomic write: write to temp, then rename
        self._write_json_with_retry(temp_file, data)

        # Use replace for atomic operation
        if os.path.exists(state_file):
            os.replace(temp_file, state_file)
        else:
            os.rename(temp_file, state_file)

        get_logger().info(f"Updated round={new_round}, stage={new_stage}")

    def get_bootnodes(self) -> List[str]:
        """
        Get bootnode addresses (compatibility method).
        In GDrive mode, this returns empty list as discovery is handled separately.

        Returns:
            Empty list (discovery handled by GDrivePeerDiscovery)
        """
        return []

    def _read_json_with_retry(self, filepath: str, max_retries: int = 3) -> dict:
        """
        Read JSON file with retry logic for GDrive API limits.

        Args:
            filepath: Path to JSON file
            max_retries: Maximum number of retry attempts

        Returns:
            Parsed JSON as dictionary, or empty dict on failure
        """
        for attempt in range(max_retries):
            try:
                if not os.path.exists(filepath):
                    get_logger().debug(f"File does not exist: {filepath}")
                    return {}

                with open(filepath, 'r') as f:
                    return json.load(f)

            except (json.JSONDecodeError, FileNotFoundError) as e:
                if attempt == max_retries - 1:
                    get_logger().error(f"Failed to read {filepath} after {max_retries} attempts: {e}")
                    return {}
                get_logger().debug(f"Retry {attempt + 1}/{max_retries} for reading {filepath}")
                time.sleep(2 ** attempt)  # Exponential backoff

            except Exception as e:
                get_logger().error(f"Unexpected error reading {filepath}: {e}")
                return {}

        return {}

    def _write_json_with_retry(self, filepath: str, data: dict, max_retries: int = 3):
        """
        Write JSON file with retry logic for GDrive API limits.

        Args:
            filepath: Path to JSON file
            data: Dictionary to write
            max_retries: Maximum number of retry attempts

        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(max_retries):
            try:
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
                return

            except Exception as e:
                if attempt == max_retries - 1:
                    get_logger().error(f"Failed to write {filepath} after {max_retries} attempts: {e}")
                    raise
                get_logger().debug(f"Retry {attempt + 1}/{max_retries} for writing {filepath}")
                time.sleep(2 ** attempt)  # Exponential backoff

    def get_active_peers(self) -> List[str]:
        """
        Get list of active peer IDs.

        Returns:
            List of peer IDs that have registered
        """
        peers_dir = os.path.join(self.gdrive_path, 'peers')

        if not os.path.exists(peers_dir):
            return []

        try:
            peer_files = [f for f in os.listdir(peers_dir) if f.endswith('.json')]
            peer_ids = [f.replace('.json', '') for f in peer_files]
            return peer_ids
        except Exception as e:
            get_logger().error(f"Error getting active peers: {e}")
            return []

    def get_submissions_for_round(self, round_num: int, stage_num: int) -> List[str]:
        """
        Get peer IDs that have submitted rewards for a specific round/stage.

        Args:
            round_num: Round number
            stage_num: Stage number

        Returns:
            List of peer IDs that submitted
        """
        rewards_dir = os.path.join(self.gdrive_path, 'rewards', f'round_{round_num}', f'stage_{stage_num}')

        if not os.path.exists(rewards_dir):
            return []

        try:
            reward_files = [f for f in os.listdir(rewards_dir) if f.endswith('.json')]
            peer_ids = [f.replace('.json', '') for f in reward_files]
            return peer_ids
        except Exception as e:
            get_logger().error(f"Error getting submissions for round {round_num}, stage {stage_num}: {e}")
            return []


def init_experiment(gdrive_base_path: str, experiment_name: str, config_overrides: Optional[dict] = None) -> str:
    """
    Initialize a new experiment in Google Drive.

    Args:
        gdrive_base_path: Base path (e.g., /content/drive/MyDrive/rl-swarm)
        experiment_name: Unique experiment identifier
        config_overrides: Optional dict of config overrides

    Returns:
        Path to experiment directory
    """
    exp_path = os.path.join(gdrive_base_path, 'experiments', experiment_name)

    # Create directory structure
    directories = ['state', 'peers', 'rewards', 'winners', 'checkpoints', 'logs']

    for d in directories:
        os.makedirs(os.path.join(exp_path, d), exist_ok=True)

    # Initialize state
    state = {
        "round": 0,
        "stage": 0,
        "created_at": time.time(),
        "experiment_name": experiment_name,
        "config_overrides": config_overrides or {}
    }

    state_file = os.path.join(exp_path, 'state', 'current_state.json')
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

    # Save config overrides if provided
    if config_overrides:
        import yaml
        config_file = os.path.join(exp_path, 'config.yaml')
        with open(config_file, 'w') as f:
            yaml.dump(config_overrides, f)

    get_logger().info(f"Initialized experiment: {experiment_name} at {exp_path}")
    return exp_path
