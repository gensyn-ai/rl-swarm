"""
Google Drive Logger for RL Swarm

Handles comprehensive logging to Google Drive including:
- Training metrics (JSONL format)
- Model checkpoints
- Training events
"""

import json
import os
import shutil
import time
from typing import Dict, Any, Optional
import torch
from genrl.logging_utils.global_defs import get_logger


class GDriveLogger:
    """
    Handles all logging to Google Drive including:
    - Training metrics (JSONL format)
    - Checkpoints
    - Training events
    """

    def __init__(self, gdrive_log_path: str, node_id: str, experiment_name: str):
        """
        Initialize Google Drive logger.

        Args:
            gdrive_log_path: Path to experiment logs (e.g., /drive/.../experiments/exp1/logs/worker_1/)
            node_id: Unique node identifier (e.g., 'worker_1')
            experiment_name: Name of experiment
        """
        self.gdrive_log_path = gdrive_log_path
        self.node_id = node_id
        self.experiment_name = experiment_name

        os.makedirs(gdrive_log_path, exist_ok=True)

        self.metrics_file = os.path.join(gdrive_log_path, 'metrics.jsonl')
        self.events_file = os.path.join(gdrive_log_path, 'training_events.jsonl')

        # Checkpoint directory is one level up from logs
        log_parent = os.path.dirname(gdrive_log_path.rstrip('/'))
        self.checkpoint_dir = os.path.join(os.path.dirname(log_parent), 'checkpoints')

        get_logger().info(f"Initialized GDrive logger for {node_id} in experiment {experiment_name}")

    def log_metrics(self, round_num: int, stage_num: int, metrics_dict: Dict[str, Any]):
        """
        Log metrics in JSONL format (newline-delimited JSON).
        Allows streaming aggregation and analysis.

        Args:
            round_num: Current round number
            stage_num: Current stage number
            metrics_dict: Dictionary of metrics to log
        """
        entry = {
            "timestamp": time.time(),
            "round": round_num,
            "stage": stage_num,
            "node_id": self.node_id,
            "experiment": self.experiment_name,
            **metrics_dict
        }

        try:
            with open(self.metrics_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            get_logger().error(f"Failed to log metrics: {e}")

    def log_checkpoint(self, round_num: int, model, optimizer: Optional[Any] = None, **extra_state):
        """
        Save model checkpoint to Google Drive.

        Args:
            round_num: Current round number
            model: PyTorch model to save
            optimizer: Optional optimizer to save
            **extra_state: Additional state to save in checkpoint
        """
        checkpoint_round_dir = os.path.join(self.checkpoint_dir, f'round_{round_num}')
        os.makedirs(checkpoint_round_dir, exist_ok=True)

        checkpoint_path = os.path.join(checkpoint_round_dir, f'{self.node_id}.pt')

        checkpoint = {
            "round": round_num,
            "node_id": self.node_id,
            "experiment": self.experiment_name,
            "model_state_dict": model.state_dict(),
            "timestamp": time.time(),
            **extra_state
        }

        if optimizer is not None:
            checkpoint["optimizer_state_dict"] = optimizer.state_dict()

        try:
            torch.save(checkpoint, checkpoint_path)
            get_logger().info(f"Saved checkpoint to {checkpoint_path}")
        except Exception as e:
            get_logger().error(f"Failed to save checkpoint: {e}")

    def load_checkpoint(self, round_num: int, model, optimizer: Optional[Any] = None) -> Optional[Dict]:
        """
        Load checkpoint from Google Drive.

        Args:
            round_num: Round number to load
            model: PyTorch model to load state into
            optimizer: Optional optimizer to load state into

        Returns:
            Checkpoint dictionary if successful, None otherwise
        """
        checkpoint_path = os.path.join(
            self.checkpoint_dir,
            f'round_{round_num}',
            f'{self.node_id}.pt'
        )

        if not os.path.exists(checkpoint_path):
            get_logger().warning(f"No checkpoint found at {checkpoint_path}")
            return None

        try:
            checkpoint = torch.load(checkpoint_path)
            model.load_state_dict(checkpoint["model_state_dict"])

            if optimizer is not None and "optimizer_state_dict" in checkpoint:
                optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

            get_logger().info(f"Loaded checkpoint from round {round_num}")
            return checkpoint

        except Exception as e:
            get_logger().error(f"Failed to load checkpoint: {e}")
            return None

    def find_latest_checkpoint(self) -> Optional[int]:
        """
        Find the latest checkpoint round for this node.

        Returns:
            Latest checkpoint round number, or None if no checkpoints exist
        """
        if not os.path.exists(self.checkpoint_dir):
            return None

        try:
            round_dirs = [d for d in os.listdir(self.checkpoint_dir) if d.startswith('round_')]
            checkpoint_rounds = []

            for round_dir in round_dirs:
                checkpoint_file = os.path.join(
                    self.checkpoint_dir,
                    round_dir,
                    f'{self.node_id}.pt'
                )
                if os.path.exists(checkpoint_file):
                    round_num = int(round_dir.replace('round_', ''))
                    checkpoint_rounds.append(round_num)

            if checkpoint_rounds:
                latest_round = max(checkpoint_rounds)
                get_logger().info(f"Found latest checkpoint at round {latest_round}")
                return latest_round

            return None

        except Exception as e:
            get_logger().error(f"Error finding latest checkpoint: {e}")
            return None

    def log_event(self, event_type: str, data: Dict[str, Any]):
        """
        Log training events (errors, warnings, state changes).

        Args:
            event_type: Type of event (e.g., 'error', 'warning', 'round_start')
            data: Event data dictionary
        """
        entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "node_id": self.node_id,
            "experiment": self.experiment_name,
            "data": data
        }

        try:
            with open(self.events_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            get_logger().error(f"Failed to log event: {e}")

    def log_system_info(self, system_info: Dict[str, Any]):
        """
        Log system information to a dedicated file.

        Args:
            system_info: Dictionary with system information
        """
        system_info_file = os.path.join(self.gdrive_log_path, 'system_info.json')

        try:
            with open(system_info_file, 'w') as f:
                json.dump(system_info, f, indent=2)
            get_logger().info(f"Logged system info to {system_info_file}")
        except Exception as e:
            get_logger().error(f"Failed to log system info: {e}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics from logged metrics.

        Returns:
            Dictionary with summary statistics
        """
        if not os.path.exists(self.metrics_file):
            return {}

        try:
            metrics = []
            with open(self.metrics_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        metrics.append(entry)
                    except json.JSONDecodeError:
                        continue

            if not metrics:
                return {}

            rounds = [m['round'] for m in metrics]
            return {
                "total_entries": len(metrics),
                "min_round": min(rounds),
                "max_round": max(rounds),
                "node_id": self.node_id,
                "experiment": self.experiment_name
            }

        except Exception as e:
            get_logger().error(f"Error getting metrics summary: {e}")
            return {}
