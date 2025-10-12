"""
Test results saver for TEST_MODE validation.

Saves validation results to Google Drive for easy review and comparison.
"""

import json
import os
import time
from typing import Dict, Any, Optional


class TestResultsSaver:
    """
    Saves test validation results to Google Drive.

    Creates a test_results.json file with validation status,
    timestamps, and detailed check results.
    """

    def __init__(self, gdrive_path: str, experiment_name: str):
        """
        Initialize test results saver.

        Args:
            gdrive_path: Base Google Drive path
            experiment_name: Experiment name
        """
        self.gdrive_path = gdrive_path
        self.experiment_name = experiment_name

        # Results file path
        self.exp_dir = os.path.join(gdrive_path, 'experiments', experiment_name)
        os.makedirs(self.exp_dir, exist_ok=True)

        self.results_file = os.path.join(self.exp_dir, 'test_results.json')

    def save_results(
        self,
        checks: Dict[str, bool],
        config: Dict[str, Any],
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Save test validation results.

        Args:
            checks: Dictionary of check names to pass/fail status
            config: Test configuration (nodes, rounds, I, J, etc.)
            details: Optional detailed results from each check
        """
        results = {
            'experiment': self.experiment_name,
            'timestamp': time.time(),
            'timestamp_iso': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            'overall_pass': all(checks.values()),
            'checks': checks,
            'config': config
        }

        if details:
            results['details'] = details

        # Write results
        try:
            with open(self.results_file, 'w') as f:
                json.dump(results, f, indent=2)
                f.flush()
                os.fsync(f.fileno())

            status = "✅ PASSED" if results['overall_pass'] else "❌ FAILED"
            print(f"\n📊 Test results saved to: {self.results_file}")
            print(f"   Status: {status}")
            print(f"   Checks: {sum(checks.values())}/{len(checks)} passed")
        except Exception as e:
            print(f"⚠ Failed to save test results: {e}")

    def load_results(self) -> Optional[Dict[str, Any]]:
        """
        Load existing test results.

        Returns:
            Test results dictionary, or None if not found
        """
        if not os.path.exists(self.results_file):
            return None

        try:
            with open(self.results_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠ Failed to load test results: {e}")
            return None


def save_test_results(
    gdrive_path: str,
    experiment_name: str,
    state_check: bool,
    submissions_check: bool,
    logs_check: bool,
    coordinator_check: bool,
    rollouts_check: Optional[bool] = None,
    num_nodes: int = 5,
    num_rounds: int = 3,
    num_train_samples: int = 4,
    num_transplants: int = 0,
    details: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Convenience function to save test results.

    Args:
        gdrive_path: Base Google Drive path
        experiment_name: Experiment name
        state_check: State file validation result
        submissions_check: Submissions validation result
        logs_check: Logs validation result
        coordinator_check: Coordinator validation result
        rollouts_check: Rollouts validation result (None to skip)
        num_nodes: Number of nodes
        num_rounds: Number of rounds
        num_train_samples: I value
        num_transplants: J value
        details: Optional detailed results

    Returns:
        True if all checks passed, False otherwise
    """
    checks = {
        'state_file': state_check,
        'submissions': submissions_check,
        'logs': logs_check,
        'coordinator': coordinator_check
    }

    if rollouts_check is not None:
        checks['rollouts'] = rollouts_check

    config = {
        'num_nodes': num_nodes,
        'num_rounds': num_rounds,
        'num_train_samples': num_train_samples,
        'num_transplants': num_transplants
    }

    saver = TestResultsSaver(gdrive_path, experiment_name)
    saver.save_results(checks, config, details)

    return all(checks.values())


def compare_test_results(gdrive_path: str, experiment_names: list[str]) -> Dict[str, Any]:
    """
    Compare results from multiple test runs.

    Args:
        gdrive_path: Base Google Drive path
        experiment_names: List of experiment names to compare

    Returns:
        Dictionary with comparison data
    """
    comparison = {
        'experiments': {},
        'summary': {
            'total': len(experiment_names),
            'passed': 0,
            'failed': 0
        }
    }

    for exp_name in experiment_names:
        saver = TestResultsSaver(gdrive_path, exp_name)
        results = saver.load_results()

        if results:
            comparison['experiments'][exp_name] = {
                'overall_pass': results.get('overall_pass'),
                'timestamp': results.get('timestamp_iso'),
                'checks_passed': sum(results.get('checks', {}).values()),
                'checks_total': len(results.get('checks', {}))
            }

            if results.get('overall_pass'):
                comparison['summary']['passed'] += 1
            else:
                comparison['summary']['failed'] += 1
        else:
            comparison['experiments'][exp_name] = {'error': 'No results found'}

    return comparison


def print_test_summary(gdrive_path: str, experiment_names: list[str]):
    """
    Print a formatted summary of test results.

    Args:
        gdrive_path: Base Google Drive path
        experiment_names: List of experiment names
    """
    comparison = compare_test_results(gdrive_path, experiment_names)

    print("=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    print(f"Total experiments: {comparison['summary']['total']}")
    print(f"Passed: {comparison['summary']['passed']} ✅")
    print(f"Failed: {comparison['summary']['failed']} ❌")
    print()

    for exp_name, data in comparison['experiments'].items():
        if 'error' in data:
            print(f"  {exp_name}: {data['error']}")
        else:
            status = "✅" if data['overall_pass'] else "❌"
            print(f"  {status} {exp_name}")
            print(f"     {data['checks_passed']}/{data['checks_total']} checks passed")
            print(f"     Run at: {data['timestamp']}")
            print()

    print("=" * 70)
