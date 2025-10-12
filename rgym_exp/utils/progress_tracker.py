"""
Training progress tracking to Google Drive.

Tracks training progress in real-time and saves to Google Drive,
allowing monitoring even after disconnection.
"""

import json
import os
import time
from typing import Dict, Any, Optional
import torch


class ProgressTracker:
    """
    Tracks training progress and saves to Google Drive.

    Creates a progress.jsonl file with one line per update,
    allowing easy monitoring and analysis.
    """

    def __init__(self, gdrive_path: str, experiment_name: str, node_id: str):
        """
        Initialize progress tracker.

        Args:
            gdrive_path: Base Google Drive path
            experiment_name: Experiment name
            node_id: Node identifier
        """
        self.gdrive_path = gdrive_path
        self.experiment_name = experiment_name
        self.node_id = node_id

        # Progress file path
        exp_dir = os.path.join(gdrive_path, 'experiments', experiment_name)
        os.makedirs(exp_dir, exist_ok=True)

        self.progress_file = os.path.join(exp_dir, f'progress_{node_id}.jsonl')

        # Track start time
        self.start_time = time.time()

        # Write initial entry
        self._log_progress({
            'event': 'training_started',
            'node_id': node_id,
            'experiment': experiment_name
        })

    def _log_progress(self, data: Dict[str, Any]):
        """
        Write progress entry to file.

        Args:
            data: Progress data dictionary
        """
        entry = {
            'timestamp': time.time(),
            'elapsed_seconds': time.time() - self.start_time,
            **data
        }

        try:
            with open(self.progress_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
        except Exception as e:
            print(f"⚠ Failed to log progress: {e}")

    def log_round_start(self, round_num: int, stage_num: int = 0):
        """
        Log start of a training round.

        Args:
            round_num: Round number
            stage_num: Stage number (default 0)
        """
        data = {
            'event': 'round_start',
            'round': round_num,
            'stage': stage_num,
            'node_id': self.node_id
        }

        # Add GPU memory if available
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated(0) / 1e9
            reserved = torch.cuda.memory_reserved(0) / 1e9
            total = torch.cuda.get_device_properties(0).total_memory / 1e9

            data['gpu_memory_gb'] = {
                'allocated': round(allocated, 2),
                'reserved': round(reserved, 2),
                'total': round(total, 2),
                'utilization_percent': round((reserved / total) * 100, 1)
            }

        self._log_progress(data)

    def log_round_complete(
        self,
        round_num: int,
        stage_num: int = 0,
        reward: Optional[float] = None,
        metrics: Optional[Dict[str, Any]] = None
    ):
        """
        Log completion of a training round.

        Args:
            round_num: Round number
            stage_num: Stage number
            reward: Round reward (optional)
            metrics: Additional metrics (optional)
        """
        data = {
            'event': 'round_complete',
            'round': round_num,
            'stage': stage_num,
            'node_id': self.node_id
        }

        if reward is not None:
            data['reward'] = round(reward, 4)

        if metrics:
            data['metrics'] = metrics

        self._log_progress(data)

    def log_training_complete(self, total_rounds: int, final_metrics: Optional[Dict[str, Any]] = None):
        """
        Log training completion.

        Args:
            total_rounds: Total number of rounds completed
            final_metrics: Final metrics summary (optional)
        """
        data = {
            'event': 'training_complete',
            'total_rounds': total_rounds,
            'node_id': self.node_id,
            'total_elapsed_seconds': time.time() - self.start_time
        }

        if final_metrics:
            data['final_metrics'] = final_metrics

        self._log_progress(data)

    def log_error(self, error_type: str, error_message: str, round_num: Optional[int] = None):
        """
        Log an error event.

        Args:
            error_type: Type of error (e.g., 'OOM', 'timeout')
            error_message: Error message
            round_num: Round where error occurred (optional)
        """
        data = {
            'event': 'error',
            'error_type': error_type,
            'error_message': error_message,
            'node_id': self.node_id
        }

        if round_num is not None:
            data['round'] = round_num

        self._log_progress(data)

    def get_latest_progress(self) -> Optional[Dict[str, Any]]:
        """
        Read the most recent progress entry.

        Returns:
            Most recent progress entry, or None if file doesn't exist
        """
        if not os.path.exists(self.progress_file):
            return None

        try:
            with open(self.progress_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    return json.loads(lines[-1])
        except Exception as e:
            print(f"⚠ Failed to read progress: {e}")

        return None

    def get_all_progress(self) -> list[Dict[str, Any]]:
        """
        Read all progress entries.

        Returns:
            List of all progress entries
        """
        if not os.path.exists(self.progress_file):
            return []

        entries = []
        try:
            with open(self.progress_file, 'r') as f:
                for line in f:
                    entries.append(json.loads(line.strip()))
        except Exception as e:
            print(f"⚠ Failed to read progress: {e}")

        return entries


def get_experiment_progress(gdrive_path: str, experiment_name: str) -> Dict[str, Any]:
    """
    Get aggregated progress for an experiment (all nodes).

    Args:
        gdrive_path: Base Google Drive path
        experiment_name: Experiment name

    Returns:
        Dictionary with aggregated progress information
    """
    exp_dir = os.path.join(gdrive_path, 'experiments', experiment_name)

    if not os.path.exists(exp_dir):
        return {'error': 'Experiment not found'}

    # Find all progress files
    progress_files = [
        f for f in os.listdir(exp_dir)
        if f.startswith('progress_') and f.endswith('.jsonl')
    ]

    if not progress_files:
        return {'error': 'No progress files found'}

    # Aggregate data from all nodes
    all_nodes = {}

    for progress_file in progress_files:
        node_id = progress_file.replace('progress_', '').replace('.jsonl', '')
        file_path = os.path.join(exp_dir, progress_file)

        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                if lines:
                    latest = json.loads(lines[-1])
                    all_nodes[node_id] = {
                        'latest_event': latest.get('event'),
                        'latest_round': latest.get('round'),
                        'elapsed_seconds': latest.get('elapsed_seconds'),
                        'last_update': latest.get('timestamp')
                    }
        except Exception as e:
            all_nodes[node_id] = {'error': str(e)}

    return {
        'experiment': experiment_name,
        'nodes': all_nodes,
        'timestamp': time.time()
    }
