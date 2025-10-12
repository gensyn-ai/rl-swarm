import os
import time
from collections import defaultdict

from genrl.communication import Communication
from genrl.data import DataManager
from genrl.game import BaseGameManager
from genrl.game.game_manager import DefaultGameManagerMixin
from genrl.logging_utils.global_defs import get_logger
from genrl.logging_utils.system_utils import get_system_info
from genrl.rewards import RewardManager
from genrl.roles import RoleManager
from genrl.state import GameState
from genrl.trainer import TrainerModule
from huggingface_hub import login, whoami

from rgym_exp.src.utils.name_utils import get_name_from_peer_id
from rgym_exp.communication.gdrive_backend import GDriveCommunicationBackend


class SwarmGameManager(BaseGameManager, DefaultGameManagerMixin):
    """GameManager that orchestrates RL Swarm training using Google Drive coordination."""

    def __init__(
        self,
        coordinator=None,  # GDriveSwarmCoordinator or None
        max_stage: int = 1,
        max_round: int = 1000000,
        game_state: GameState = None,
        reward_manager: RewardManager = None,
        trainer: TrainerModule = None,
        data_manager: DataManager = None,
        communication: Communication = None,
        role_manager: RoleManager | None = None,
        run_mode: str = "train",
        log_dir: str = "logs",
        hf_token: str | None = None,
        hf_push_frequency: int = 20,
        **kwargs,
    ):

        super().__init__(
            max_stage=max_stage,
            max_round=max_round,
            game_state=game_state,
            reward_manager=reward_manager,
            trainer=trainer,
            data_manager=data_manager,
            communication=communication,
            role_manager=role_manager,
            run_mode=run_mode,
        )

        # Google Drive mode only - validate communication backend
        assert isinstance(self.communication, GDriveCommunicationBackend)
        self.train_timeout = 60 * 60 * 24 * 31  # 1 month

        # Logging Setup
        self.peer_id = self.communication.get_id()
        self.state.peer_id = self.peer_id
        self.animal_name = get_name_from_peer_id(self.peer_id, True)

        # Register peer_id and get current round from the coordinator (if available)
        self.coordinator = coordinator
        if self.coordinator is not None:
            try:
                self.coordinator.register_peer(self.peer_id)
                round, _ = self.coordinator.get_round_and_stage()
                self.state.round = round
                get_logger().info(f"Registered with coordinator at round {round}")
            except Exception as e:
                get_logger().warning(f"Failed to register with coordinator: {e}")
                self.state.round = 0
        else:
            get_logger().info("Running without coordinator (standalone mode)")
            self.state.round = 0

        self.communication.step_ = (
            self.state.round
        )  # initialize communication module to current round

        # Initialize GDrive logger if in GDrive mode
        self.gdrive_logger = None
        if log_dir and '/drive/' in log_dir:
            try:
                from rgym_exp.src.gdrive_logger import GDriveLogger
                import os
                self.gdrive_logger = GDriveLogger(
                    gdrive_log_path=log_dir,
                    node_id=os.environ.get('NODE_ID', self.peer_id[:8]),
                    experiment_name=os.environ.get('EXPERIMENT_NAME', 'default')
                )
                get_logger().info("Initialized GDrive logger")
            except Exception as e:
                get_logger().warning(f"Failed to initialize GDrive logger: {e}")

        # enable push to HF if token was provided
        self.hf_token = hf_token
        if self.hf_token not in [None, "None"]:
            self._configure_hf_hub(hf_push_frequency)

        get_logger().info(
            f"🐱 Hello 🐈 [{get_name_from_peer_id(self.peer_id)}] 🦮 [{self.peer_id}]!"
        )
        get_logger().info(f"bootnodes: {kwargs.get('bootnodes', [])}")
        get_logger().info(f"Using Model: {self.trainer.model.config.name_or_path}")

        with open(os.path.join(log_dir, f"system_info.txt"), "w") as f:
            f.write(get_system_info())

        self.batched_signals = 0.0
        self.time_since_submit = time.time()  # seconds
        self.submit_period = 3.0  # hours
        self.submitted_this_round = False

    def _get_total_rewards_by_agent(self):
        rewards_by_agent = defaultdict(int)
        for stage in range(self.state.stage):
            rewards = self.rewards[stage]
            for agent_id, agent_rewards in rewards.items():
                for batch_id, batch_rewards in agent_rewards.items():
                    tot = 0
                    for generation_rewards in batch_rewards:
                        tot += sum(generation_rewards)
                    rewards_by_agent[agent_id] += tot

        return rewards_by_agent

    def _get_my_rewards(self, signal_by_agent):
        if len(signal_by_agent) == 0:
            return 0
        if self.peer_id in signal_by_agent:
            my_signal = signal_by_agent[self.peer_id]
        else:
            my_signal = 0
        my_signal = (my_signal + 1) * (my_signal > 0) + my_signal * (my_signal <= 0)

        # Log metrics to GDrive
        if self.gdrive_logger:
            try:
                self.gdrive_logger.log_metrics(
                    self.state.round,
                    self.state.stage,
                    {
                        'my_reward': my_signal,
                        'total_agents': len(signal_by_agent),
                        'peer_id': self.peer_id
                    }
                )
            except Exception as e:
                get_logger().debug(f"Failed to log metrics: {e}")

        return my_signal

    def _try_submit_to_chain(self, signal_by_agent):
        if self.coordinator is None:
            return  # Skip if no coordinator

        elapsed_time_hours = (time.time() - self.time_since_submit) / 3600
        if elapsed_time_hours > self.submit_period:
            try:
                self.coordinator.submit_reward(
                    self.state.round, 0, int(self.batched_signals), self.peer_id
                )
                self.batched_signals = 0.0
                if len(signal_by_agent) > 0:
                    max_agent, max_signal = max(
                        signal_by_agent.items(), key=lambda x: x[1]
                    )
                else:  # if we have no signal_by_agents, just submit ourselves.
                    max_agent = self.peer_id

                self.coordinator.submit_winners(
                    self.state.round, [max_agent], self.peer_id
                )
                self.time_since_submit = time.time()
                self.submitted_this_round = True
            except Exception as e:
                get_logger().error(f"Failed to submit to coordinator: {e}")

    def _hook_after_rewards_updated(self):
        signal_by_agent = self._get_total_rewards_by_agent()
        self.batched_signals += self._get_my_rewards(signal_by_agent)
        self._try_submit_to_chain(signal_by_agent)

    def _hook_after_round_advanced(self):
        self._save_to_hf()

        # Try to submit to chain again if necessary, but don't update our signal twice
        if not self.submitted_this_round:
            signal_by_agent = self._get_total_rewards_by_agent()
            self._try_submit_to_chain(signal_by_agent)

        # Reset flag for next round
        self.submitted_this_round = False

        # Notify GDrive backend that round has advanced (triggers cleanup & buffered publish)
        if isinstance(self.communication, GDriveCommunicationBackend):
            self.communication.advance_round()

        # Block until swarm round advances
        self.agent_block()

    def _hook_after_game(self):
        self._save_to_hf()

        # Save checkpoint to GDrive if enabled
        checkpoint_interval = int(os.environ.get('CHECKPOINT_INTERVAL', '10'))
        if self.gdrive_logger and checkpoint_interval > 0 and self.state.round % checkpoint_interval == 0:
            try:
                self.gdrive_logger.log_checkpoint(
                    self.state.round,
                    self.trainer.model,
                    self.trainer.optimizer if hasattr(self.trainer, 'optimizer') else None
                )
            except Exception as e:
                get_logger().error(f"Failed to save checkpoint: {e}")

    def _configure_hf_hub(self, hf_push_frequency):
        username = whoami(token=self.hf_token)["name"]
        model_name = self.trainer.model.config.name_or_path.split("/")[-1]
        model_name += "-Gensyn-Swarm"
        model_name += f"-{self.animal_name}"
        self.trainer.args.hub_model_id = f"{username}/{model_name}"
        self.hf_push_frequency = hf_push_frequency
        get_logger().info("Logging into Hugging Face Hub...")
        login(self.hf_token)

    def _save_to_hf(self):
        if (
            self.hf_token not in [None, "None"]
            and self.state.round % self.hf_push_frequency == 0
        ):
            get_logger().info(f"pushing model to huggingface")
            try:
                repo_id = self.trainer.args.hub_model_id

                self.trainer.model.push_to_hub(
                    repo_id=repo_id,
                    token=self.hf_token,
                    commit_message=f"rl-swarm: round {self.state.round}, agent {self.animal_name}",
                    tags=[
                        "rl-swarm",
                        "genrl-swarm",
                        "grpo",
                        "gensyn",
                        f"I am {self.animal_name}",
                    ],
                )
            except Exception:
                get_logger().exception(
                    "Failed to push model to the Hugging Face Hub. When you conclude training please try manually pushing it yourself using the instructions here: https://huggingface.co/docs/hub/en/models-uploading",
                    stack_info=True,
                )

    def agent_block(
        self, check_interval=5.0, log_timeout=10.0, max_check_interval=60.0 * 15
    ):
        # Coordinator advances the round when it finishes
        if self.coordinator is not None and self.coordinator.node_role == 'coordinator':
            try:
                next_round = self.state.round + 1
                self.coordinator.update_round_stage(next_round, 0)
                get_logger().info(f"📝 Coordinator advanced global state to round {next_round}")
            except Exception as e:
                get_logger().error(f"Coordinator failed to advance round: {e}")

        start_time = time.monotonic()
        fetch_log_time = start_time
        check_backoff = (
            check_interval  # Exponential backoff for already finished rounds.
        )
        while time.monotonic() - start_time < self.train_timeout:
            curr_time = time.monotonic()

            # Retrieve current round and stage.
            try:
                if self.coordinator is not None:
                    round_num, stage = self.coordinator.get_round_and_stage()
                else:
                    # In standalone mode, just use current state
                    round_num, stage = self.state.round, self.state.stage
            except Exception as e:
                if curr_time - fetch_log_time > log_timeout:
                    get_logger().debug(
                        f"Could not fetch round and stage: {e}. Next check in {check_interval}s."
                    )
                    fetch_log_time = curr_time

                time.sleep(check_interval)
                continue

            if round_num >= self.state.round:
                get_logger().info(f"🐝 Joining round: {round_num}")
                check_backoff = check_interval  # Reset backoff after successful round
                self.state.round = round_num  # advance to swarm's round.
                return
            else:
                get_logger().info(
                    f"Already finished round: {round_num}. Next check in {check_backoff}s."
                )
                time.sleep(check_backoff)
                check_backoff = min(check_backoff * 2, max_check_interval)

            if round_num == self.max_round - 1:
                return

        get_logger().info("Training timed out!")

    def run_coordinator_loop(self):
        """
        Coordinator-only loop: manages round advancement without training.

        The coordinator:
        1. Initializes the global state
        2. Waits for worker activity (or timeout)
        3. Advances rounds automatically
        4. Logs progress
        5. No training, minimal GPU usage
        """
        if self.coordinator is None or self.coordinator.node_role != 'coordinator':
            raise ValueError("run_coordinator_loop() can only be called by coordinator")

        get_logger().info("="*60)
        get_logger().info("🎯 Starting Coordinator Loop (non-training mode)")
        get_logger().info("="*60)

        current_round = 0
        round_advance_interval = int(os.environ.get('COORDINATOR_ROUND_INTERVAL', '60'))  # seconds

        start_time = time.time()

        while current_round < self.max_round:
            # Wait for workers to complete round (or timeout)
            get_logger().info(f"📊 Round {current_round}: Waiting {round_advance_interval}s for workers...")
            time.sleep(round_advance_interval)

            # Check how many workers have submitted
            try:
                submissions = self.coordinator.get_submissions_for_round(current_round, 0)
                active_peers = self.coordinator.get_active_peers()
                get_logger().info(
                    f"📥 Round {current_round}: {len(submissions)}/{len(active_peers)} workers submitted"
                )
            except Exception as e:
                get_logger().warning(f"Failed to check submissions: {e}")

            # Advance to next round
            current_round += 1
            try:
                self.coordinator.update_round_stage(current_round, 0)
                elapsed = time.time() - start_time
                get_logger().info(
                    f"✅ Advanced to round {current_round} (elapsed: {elapsed/60:.1f}m)"
                )
            except Exception as e:
                get_logger().error(f"Failed to advance round: {e}")
                break

        total_time = time.time() - start_time
        get_logger().info("="*60)
        get_logger().info(f"🏁 Coordinator finished {self.max_round} rounds in {total_time/60:.1f}m")
        get_logger().info("="*60)
