"""
Validation script for TEST_MODE runs.

This script checks the outputs of a test mode run to ensure:
1. State file exists and shows correct round
2. Worker submissions are present
3. Logs are generated for all nodes
4. No OOM errors occurred
5. Coordinator advanced rounds properly

Usage:
    python rgym_exp/test/validate_test_run.py --gdrive-path /content/drive/MyDrive/rl-swarm --experiment test_mode_validation
"""

import argparse
import json
import os
import sys
from pathlib import Path


def validate_state_file(exp_path, expected_rounds=3):
    """Validate that state file exists and reached expected round."""
    state_file = os.path.join(exp_path, 'state', 'current_state.json')

    if not os.path.exists(state_file):
        print(f"✗ State file not found at {state_file}")
        return False

    try:
        with open(state_file, 'r') as f:
            state = json.load(f)

        current_round = state.get('round', -1)
        print(f"✓ State file exists: Round {current_round}")

        if current_round == expected_rounds:
            print(f"  ✓ Reached round {expected_rounds} as expected")
            return True
        else:
            print(f"  ⚠ Expected round {expected_rounds}, got {current_round}")
            return False
    except Exception as e:
        print(f"✗ Error reading state file: {e}")
        return False


def validate_submissions(exp_path, num_rounds=3):
    """Validate that worker submissions exist for all rounds."""
    all_valid = True

    for round_num in range(num_rounds):
        submissions_dir = os.path.join(exp_path, 'rewards', f'round_{round_num}', 'stage_0')

        if not os.path.exists(submissions_dir):
            print(f"✗ Round {round_num}: No submissions directory")
            all_valid = False
            continue

        submissions = [f for f in os.listdir(submissions_dir) if f.endswith('.json')]

        if len(submissions) > 0:
            print(f"✓ Round {round_num}: {len(submissions)} worker submissions")
        else:
            print(f"⚠ Round {round_num}: No submissions found")
            all_valid = False

    return all_valid


def validate_logs(exp_path, num_nodes=5):
    """Validate that logs exist for all nodes."""
    all_valid = True

    for i in range(num_nodes):
        log_dir = os.path.join(exp_path, 'logs', f'node_{i}')
        stdout_log = os.path.join(log_dir, 'stdout.log')
        stderr_log = os.path.join(log_dir, 'stderr.log')

        if os.path.exists(stdout_log):
            print(f"✓ Node {i}: stdout.log present")
        else:
            print(f"✗ Node {i}: stdout.log missing")
            all_valid = False

        if os.path.exists(stderr_log):
            # Check for OOM errors
            with open(stderr_log, 'r') as f:
                stderr_content = f.read()

            if 'OutOfMemoryError' in stderr_content or 'CUDA out of memory' in stderr_content:
                print(f"  ⚠ Node {i}: OOM error detected in stderr.log")
                all_valid = False
            else:
                print(f"  ✓ Node {i}: No OOM errors")

    return all_valid


def validate_coordinator_logs(exp_path):
    """Validate coordinator-specific functionality."""
    coord_log = os.path.join(exp_path, 'logs', 'node_0', 'stdout.log')

    if not os.path.exists(coord_log):
        print("✗ Coordinator log not found")
        return False

    with open(coord_log, 'r') as f:
        log_content = f.read()

    # Check for coordinator-specific messages
    checks = {
        'Coordinator loop started': '🎯 Starting Coordinator Loop' in log_content,
        'Round advancement': '📝 Coordinator advanced global state to round' in log_content or '✅ Advanced to round' in log_content,
        'Worker monitoring': '📊 Round' in log_content and 'Waiting' in log_content,
    }

    all_valid = True
    for check_name, passed in checks.items():
        if passed:
            print(f"✓ Coordinator: {check_name}")
        else:
            print(f"✗ Coordinator: {check_name} not found")
            all_valid = False

    return all_valid


def validate_rollouts(exp_path, num_rounds=3, num_transplants=0, num_workers=4):
    """
    Validate rollout sharing (for configs with J > 0).

    Args:
        exp_path: Path to experiment directory
        num_rounds: Number of rounds to check
        num_transplants: Expected J value (0 means skip validation)
        num_workers: Number of training workers (excludes coordinator)

    Returns:
        True if validation passes, False otherwise
    """
    if num_transplants == 0:
        print("⊘ Rollout validation skipped (J=0, no sharing expected)")
        return True

    all_valid = True

    for round_num in range(num_rounds):
        rollouts_dir = os.path.join(exp_path, 'rollouts', f'round_{round_num}', 'stage_0')

        if not os.path.exists(rollouts_dir):
            print(f"✗ Round {round_num}: No rollouts directory")
            all_valid = False
            continue

        rollout_files = [f for f in os.listdir(rollouts_dir) if f.endswith('.json')]

        if len(rollout_files) == 0:
            print(f"⚠ Round {round_num}: No rollout files (expected {num_workers})")
            all_valid = False
        elif len(rollout_files) < num_workers:
            print(f"⚠ Round {round_num}: {len(rollout_files)} rollouts (expected {num_workers})")
            all_valid = False
        else:
            # Validate rollout file structure
            valid_files = 0
            for rollout_file in rollout_files:
                file_path = os.path.join(rollouts_dir, rollout_file)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)

                    # Check required fields
                    required_fields = ['peer_id', 'round', 'stage', 'rollouts']
                    if all(field in data for field in required_fields):
                        valid_files += 1
                    else:
                        print(f"  ⚠ {rollout_file}: Missing required fields")
                        all_valid = False
                except Exception as e:
                    print(f"  ✗ {rollout_file}: Failed to parse ({e})")
                    all_valid = False

            if valid_files == num_workers:
                print(f"✓ Round {round_num}: {valid_files} rollouts published")
            else:
                print(f"⚠ Round {round_num}: {valid_files}/{num_workers} valid rollouts")
                all_valid = False

    return all_valid


def main():
    parser = argparse.ArgumentParser(description='Validate TEST_MODE run outputs')
    parser.add_argument('--gdrive-path', default='/content/drive/MyDrive/rl-swarm',
                        help='Base GDrive path')
    parser.add_argument('--experiment', default='test_mode_validation',
                        help='Experiment name')
    parser.add_argument('--rounds', type=int, default=3,
                        help='Expected number of rounds')
    parser.add_argument('--nodes', type=int, default=5,
                        help='Expected number of nodes (total including coordinator)')
    parser.add_argument('--transplants', type=int, default=0,
                        help='Expected J value (external rollouts per round, 0 = skip rollout validation)')

    args = parser.parse_args()

    exp_path = os.path.join(args.gdrive_path, 'experiments', args.experiment)
    num_workers = args.nodes - 1  # Exclude coordinator from worker count

    print("=" * 60)
    print("🔍 TEST MODE VALIDATION")
    print("=" * 60)
    print(f"Experiment: {args.experiment}")
    print(f"Path: {exp_path}")
    print(f"Config: {args.nodes} nodes ({num_workers} workers), J={args.transplants}")
    print("=" * 60)

    if not os.path.exists(exp_path):
        print(f"✗ Experiment path does not exist: {exp_path}")
        sys.exit(1)

    # Run all validations
    results = {
        'State file': validate_state_file(exp_path, args.rounds),
        'Submissions': validate_submissions(exp_path, args.rounds),
        'Logs': validate_logs(exp_path, args.nodes),
        'Coordinator': validate_coordinator_logs(exp_path),
        'Rollouts': validate_rollouts(exp_path, args.rounds, args.transplants, num_workers),
    }

    print("=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)

    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check_name}")

    print("=" * 60)

    if all(results.values()):
        print("✅ ALL CHECKS PASSED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ SOME CHECKS FAILED")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
