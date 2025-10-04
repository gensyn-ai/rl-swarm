"""
Coordinator Node Manager for Google Drive-based RL Swarm

This module manages round/stage progression for the coordinator node.
It monitors worker submissions and advances rounds based on configurable strategies.
"""

import os
import time
from typing import Dict, Any
from genrl.logging_utils.global_defs import get_logger


class CoordinatorManager:
    """
    Manages round progression for the coordinator node.
    Monitors worker submissions and advances rounds based on criteria.
    """

    def __init__(self, coordinator, config: Dict[str, Any]):
        """
        Initialize coordinator manager.

        Args:
            coordinator: GDriveSwarmCoordinator instance
            config: Configuration dict with advancement settings
        """
        self.coordinator = coordinator
        self.advancement_strategy = config.get('advancement_strategy', 'time_based')
        self.round_duration_minutes = config.get('round_duration_minutes', 10)
        self.min_submission_percent = config.get('min_submission_percent', 0.5)
        self.max_round_duration_minutes = config.get('max_round_duration_minutes', 20)

        self.current_round = 0
        self.current_stage = 0
        self.round_start_time = time.time()

        get_logger().info(f"Initialized Coordinator Manager with strategy: {self.advancement_strategy}")

    def run(self):
        """Main loop for coordinator"""
        get_logger().info("Starting Coordinator Manager")

        # Get initial round/stage from state
        self.current_round, self.current_stage = self.coordinator.get_round_and_stage()
        self.round_start_time = time.time()

        try:
            while True:
                try:
                    # Check if round should advance
                    if self._should_advance_round():
                        self._advance_round()

                    # Sleep before next check
                    time.sleep(30)

                except KeyboardInterrupt:
                    get_logger().info("Coordinator Manager stopped by user")
                    break
                except Exception as e:
                    get_logger().error(f"Error in coordinator loop: {e}", exc_info=True)
                    time.sleep(60)

        finally:
            get_logger().info("Coordinator Manager shutdown")

    def _should_advance_round(self) -> bool:
        """
        Determine if round should advance based on strategy.

        Returns:
            True if round should advance, False otherwise
        """
        if self.advancement_strategy == 'time_based':
            return self._check_time_based()

        elif self.advancement_strategy == 'completion_based':
            return self._check_completion_based()

        elif self.advancement_strategy == 'hybrid':
            return self._check_hybrid()

        else:
            get_logger().warning(f"Unknown advancement strategy: {self.advancement_strategy}, using time_based")
            return self._check_time_based()

    def _check_time_based(self) -> bool:
        """Check if round should advance based on time only"""
        elapsed_minutes = (time.time() - self.round_start_time) / 60
        return elapsed_minutes >= self.round_duration_minutes

    def _check_completion_based(self) -> bool:
        """Check if round should advance based on submission rate only"""
        submission_rate = self._get_submission_rate()
        return submission_rate >= self.min_submission_percent

    def _check_hybrid(self) -> bool:
        """Check if round should advance based on both time and completion"""
        elapsed_minutes = (time.time() - self.round_start_time) / 60
        submission_rate = self._get_submission_rate()

        # Advance if both conditions met
        min_met = submission_rate >= self.min_submission_percent
        time_met = elapsed_minutes >= self.round_duration_minutes

        # OR if max time exceeded (safety mechanism)
        max_time_exceeded = elapsed_minutes >= self.max_round_duration_minutes

        return (min_met and time_met) or max_time_exceeded

    def _get_submission_rate(self) -> float:
        """
        Calculate percentage of active peers that submitted.

        Returns:
            Submission rate as float between 0.0 and 1.0
        """
        try:
            # Get active peers
            active_peers = self.coordinator.get_active_peers()
            if len(active_peers) == 0:
                get_logger().debug("No active peers found")
                return 0.0

            # Get submissions for current round/stage
            submissions = self.coordinator.get_submissions_for_round(
                self.current_round,
                self.current_stage
            )

            submission_rate = len(submissions) / len(active_peers)

            get_logger().debug(
                f"Submission rate: {len(submissions)}/{len(active_peers)} "
                f"= {submission_rate:.2%}"
            )

            return submission_rate

        except Exception as e:
            get_logger().error(f"Error calculating submission rate: {e}")
            return 0.0

    def _advance_round(self):
        """Advance to next round"""
        self.current_round += 1
        self.current_stage = 0
        self.round_start_time = time.time()

        # Update state in Google Drive
        try:
            self.coordinator.update_round_stage(self.current_round, self.current_stage)
            get_logger().info(
                f"✨ Advanced to round {self.current_round}, stage {self.current_stage}"
            )
        except Exception as e:
            get_logger().error(f"Failed to advance round: {e}", exc_info=True)

    def get_status(self) -> Dict[str, Any]:
        """
        Get current coordinator status.

        Returns:
            Dictionary with status information
        """
        elapsed_minutes = (time.time() - self.round_start_time) / 60
        submission_rate = self._get_submission_rate()

        return {
            "current_round": self.current_round,
            "current_stage": self.current_stage,
            "elapsed_minutes": elapsed_minutes,
            "submission_rate": submission_rate,
            "advancement_strategy": self.advancement_strategy
        }


def main():
    """Entry point for coordinator node"""
    import hydra
    from omegaconf import DictConfig, OmegaConf
    from hydra.utils import instantiate

    @hydra.main(version_base=None, config_path="../config", config_name="colab-gdrive.yaml")
    def run_coordinator(cfg: DictConfig):
        get_logger().info("Starting Coordinator Node")
        get_logger().info(f"Config:\n{OmegaConf.to_yaml(cfg)}")

        # Create coordinator
        coordinator = instantiate(cfg.game_manager.coordinator)

        # Create and run manager
        manager_config = OmegaConf.to_container(cfg.coordinator_manager, resolve=True)
        manager = CoordinatorManager(coordinator, manager_config)

        try:
            manager.run()
        except KeyboardInterrupt:
            get_logger().info("Coordinator stopped by user")
        except Exception as e:
            get_logger().error(f"Coordinator failed: {e}", exc_info=True)
            raise

    run_coordinator()


if __name__ == "__main__":
    import os
    os.environ["HYDRA_FULL_ERROR"] = "1"
    main()
