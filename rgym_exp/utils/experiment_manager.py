"""
Experiment Management Utilities for Google Drive-based RL Swarm

Provides utilities for initializing, listing, analyzing, and managing
multiple experiments stored in Google Drive.
"""

import json
import os
import time
from typing import Dict, List, Any, Optional
import pandas as pd
import yaml
from rgym_exp.vendor.genrl.logging_utils.global_defs import get_logger


def init_experiment(
    gdrive_base_path: str,
    experiment_name: str,
    config_overrides: Optional[Dict[str, Any]] = None
) -> str:
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
    directories = [
        'state',
        'peers',
        'rewards',
        'winners',
        'checkpoints',
        'logs'
    ]

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
        config_file = os.path.join(exp_path, 'config.yaml')
        with open(config_file, 'w') as f:
            yaml.dump(config_overrides, f)

    get_logger().info(f"Initialized experiment: {experiment_name} at {exp_path}")
    return exp_path


def list_experiments(gdrive_base_path: str) -> List[Dict[str, Any]]:
    """
    List all experiments with metadata.

    Args:
        gdrive_base_path: Base path in Google Drive

    Returns:
        List of dicts with experiment info
    """
    experiments_dir = os.path.join(gdrive_base_path, 'experiments')

    if not os.path.exists(experiments_dir):
        get_logger().warning(f"Experiments directory not found: {experiments_dir}")
        return []

    experiments = []

    try:
        for exp_name in os.listdir(experiments_dir):
            exp_path = os.path.join(experiments_dir, exp_name)

            if not os.path.isdir(exp_path):
                continue

            state_file = os.path.join(exp_path, 'state', 'current_state.json')

            if not os.path.exists(state_file):
                continue

            with open(state_file, 'r') as f:
                state = json.load(f)

            # Count active peers
            peers_dir = os.path.join(exp_path, 'peers')
            num_peers = 0
            if os.path.exists(peers_dir):
                num_peers = len([f for f in os.listdir(peers_dir) if f.endswith('.json')])

            # Count checkpoints
            checkpoints_dir = os.path.join(exp_path, 'checkpoints')
            num_checkpoints = 0
            if os.path.exists(checkpoints_dir):
                num_checkpoints = len([d for d in os.listdir(checkpoints_dir) if d.startswith('round_')])

            experiments.append({
                "name": exp_name,
                "path": exp_path,
                "round": state.get('round', 0),
                "stage": state.get('stage', 0),
                "created_at": state.get('created_at'),
                "num_peers": num_peers,
                "num_checkpoints": num_checkpoints
            })

    except Exception as e:
        get_logger().error(f"Error listing experiments: {e}")

    return experiments


def get_experiment_metrics(gdrive_base_path: str, experiment_name: str) -> pd.DataFrame:
    """
    Aggregate metrics from all nodes in an experiment.

    Args:
        gdrive_base_path: Base path in Google Drive
        experiment_name: Name of experiment

    Returns:
        DataFrame with metrics from all nodes
    """
    exp_path = os.path.join(gdrive_base_path, 'experiments', experiment_name)
    logs_dir = os.path.join(exp_path, 'logs')

    if not os.path.exists(logs_dir):
        get_logger().warning(f"Logs directory not found: {logs_dir}")
        return pd.DataFrame()

    all_metrics = []

    try:
        # Read metrics from each node
        for node_dir in os.listdir(logs_dir):
            metrics_file = os.path.join(logs_dir, node_dir, 'metrics.json')

            if not os.path.exists(metrics_file):
                continue

            # Read JSONL file
            with open(metrics_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        all_metrics.append(entry)
                    except json.JSONDecodeError:
                        continue

    except Exception as e:
        get_logger().error(f"Error getting metrics: {e}")

    return pd.DataFrame(all_metrics)


def export_experiment_summary(
    gdrive_base_path: str,
    experiment_name: str,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Export experiment summary including:
    - Config
    - Final metrics
    - Peer participation
    - Round progression

    Args:
        gdrive_base_path: Base path in Google Drive
        experiment_name: Name of experiment
        output_path: Optional custom output path

    Returns:
        Summary dictionary
    """
    exp_path = os.path.join(gdrive_base_path, 'experiments', experiment_name)

    summary = {
        "experiment_name": experiment_name,
        "generated_at": time.time()
    }

    try:
        # Load state
        state_file = os.path.join(exp_path, 'state', 'current_state.json')
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                summary['final_state'] = json.load(f)

        # Load config
        config_file = os.path.join(exp_path, 'config.yaml')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                summary['config'] = yaml.safe_load(f)

        # Aggregate metrics
        metrics_df = get_experiment_metrics(gdrive_base_path, experiment_name)
        if not metrics_df.empty:
            summary['metrics_summary'] = {
                "total_rounds": int(metrics_df['round'].max()) if 'round' in metrics_df.columns else 0,
                "total_entries": len(metrics_df),
                "nodes": metrics_df['node_id'].unique().tolist() if 'node_id' in metrics_df.columns else []
            }

        # Save summary
        if output_path is None:
            output_path = os.path.join(exp_path, 'summary.json')

        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)

        get_logger().info(f"Exported summary to {output_path}")

    except Exception as e:
        get_logger().error(f"Error exporting summary: {e}")

    return summary


def compare_experiments(
    gdrive_base_path: str,
    experiment_names: List[str]
) -> pd.DataFrame:
    """
    Compare metrics across multiple experiments.

    Args:
        gdrive_base_path: Base path in Google Drive
        experiment_names: List of experiment names to compare

    Returns:
        DataFrame with comparative metrics
    """
    comparison_data = []

    for exp_name in experiment_names:
        try:
            metrics_df = get_experiment_metrics(gdrive_base_path, exp_name)

            if metrics_df.empty:
                continue

            # Aggregate metrics per round
            if 'round' in metrics_df.columns:
                round_summary = metrics_df.groupby('round').agg({
                    'timestamp': 'count',  # Number of entries
                }).reset_index()
                round_summary['experiment'] = exp_name
                comparison_data.append(round_summary)

        except Exception as e:
            get_logger().error(f"Error comparing experiment {exp_name}: {e}")

    if comparison_data:
        return pd.concat(comparison_data, ignore_index=True)
    else:
        return pd.DataFrame()


def cleanup_experiment(gdrive_base_path: str, experiment_name: str, keep_checkpoints: bool = True):
    """
    Clean up an experiment by removing logs and optionally checkpoints.

    Args:
        gdrive_base_path: Base path in Google Drive
        experiment_name: Name of experiment to clean
        keep_checkpoints: If True, keep checkpoints (default: True)
    """
    exp_path = os.path.join(gdrive_base_path, 'experiments', experiment_name)

    if not os.path.exists(exp_path):
        get_logger().warning(f"Experiment not found: {experiment_name}")
        return

    try:
        # Remove logs
        logs_dir = os.path.join(exp_path, 'logs')
        if os.path.exists(logs_dir):
            import shutil
            shutil.rmtree(logs_dir)
            get_logger().info(f"Removed logs for {experiment_name}")

        # Optionally remove checkpoints
        if not keep_checkpoints:
            checkpoints_dir = os.path.join(exp_path, 'checkpoints')
            if os.path.exists(checkpoints_dir):
                import shutil
                shutil.rmtree(checkpoints_dir)
                get_logger().info(f"Removed checkpoints for {experiment_name}")

    except Exception as e:
        get_logger().error(f"Error cleaning experiment: {e}")


def get_experiment_status(gdrive_base_path: str, experiment_name: str) -> Dict[str, Any]:
    """
    Get current status of an experiment.

    Args:
        gdrive_base_path: Base path in Google Drive
        experiment_name: Name of experiment

    Returns:
        Dictionary with experiment status
    """
    exp_path = os.path.join(gdrive_base_path, 'experiments', experiment_name)

    if not os.path.exists(exp_path):
        return {"error": "Experiment not found"}

    status = {
        "experiment_name": experiment_name,
        "checked_at": time.time()
    }

    try:
        # Get current state
        state_file = os.path.join(exp_path, 'state', 'current_state.json')
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                state = json.load(f)
                status['current_round'] = state.get('round', 0)
                status['current_stage'] = state.get('stage', 0)
                status['last_updated'] = state.get('updated_at', 0)

        # Count active peers
        peers_dir = os.path.join(exp_path, 'peers')
        if os.path.exists(peers_dir):
            peer_files = [f for f in os.listdir(peers_dir) if f.endswith('.json')]
            status['active_peers'] = len(peer_files)
            status['peer_ids'] = [f.replace('.json', '') for f in peer_files]

        # Get latest checkpoint
        checkpoints_dir = os.path.join(exp_path, 'checkpoints')
        if os.path.exists(checkpoints_dir):
            checkpoint_rounds = []
            for d in os.listdir(checkpoints_dir):
                if d.startswith('round_'):
                    round_num = int(d.replace('round_', ''))
                    checkpoint_rounds.append(round_num)
            if checkpoint_rounds:
                status['latest_checkpoint'] = max(checkpoint_rounds)

        # Get metrics summary
        metrics_df = get_experiment_metrics(gdrive_base_path, experiment_name)
        if not metrics_df.empty:
            status['total_metric_entries'] = len(metrics_df)

    except Exception as e:
        status['error'] = str(e)
        get_logger().error(f"Error getting experiment status: {e}")

    return status
