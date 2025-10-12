"""
Google Drive-Only Swarm Launcher

Simple launcher for RL Swarm using Google Drive for coordination.
No Hydra, no Hivemind, no blockchain - just environment variables and direct instantiation.
"""

import os
import uuid

from transformers import AutoModelForCausalLM
from genrl.communication.communication import Communication
from genrl.logging_utils.global_defs import get_logger
from genrl.state.game_state import GameState
from genrl.rewards import DefaultRewardManager
from genrl.rewards.reward_store import RewardFnStore, RoundRewardFnStore
from genrl.trainer.grpo_trainer import GRPOTrainerConfig

from rgym_exp.src.trainer import GRPOTrainerModule
from rgym_exp.src.data import ReasoningGymDataManager
from rgym_exp.src.rewards import RGRewards
from rgym_exp.src.manager import SwarmGameManager
from rgym_exp.src.gdrive_coordinator import GDriveSwarmCoordinator
from rgym_exp.src.gdrive_rollout_sharing import GDriveRolloutSharing
from rgym_exp.communication.gdrive_backend import GDriveCommunicationBackend
from rgym_exp.utils.gdrive_log_stream import setup_log_streaming
from rgym_exp.utils.progress_tracker import ProgressTracker


def main():
    """Main entry point for Google Drive swarm training."""

    # =======================
    # 1. Read Environment Variables
    # =======================
    gdrive_path = os.environ.get('GDRIVE_PATH', '/content/drive/MyDrive/rl-swarm')
    experiment_name = os.environ.get('EXPERIMENT_NAME', 'default_experiment')
    node_role = os.environ.get('NODE_ROLE', 'worker')  # 'coordinator' or 'worker'
    node_id = os.environ.get('NODE_ID', f'node_{uuid.uuid4().hex[:8]}')
    model_name = os.environ.get('MODEL_NAME', 'Gensyn/Qwen2.5-0.5B-Instruct')
    seed = int(os.environ.get('SEED', '42'))

    # Optional env vars
    hf_token = os.environ.get('HUGGINGFACE_ACCESS_TOKEN')

    # Check for TEST_MODE (quick validation run)
    test_mode = os.environ.get('TEST_MODE', 'False').lower() == 'true'

    # Training config (configurable via env vars for SAPO experiments)
    if test_mode:
        # Test mode: 3 rounds, small batch size for quick validation (~1-2 minutes)
        max_round = 3
        max_stage = int(os.environ.get('MAX_STAGES', '1'))
        num_generations = 4
        num_transplant_trees = int(os.environ.get('NUM_TRANSPLANT_TREES', '0'))
        num_train_samples = 4
        dtype = 'float32'
        get_logger().info("🧪 TEST MODE ENABLED: 3 rounds, 4 samples, 4 generations")
    else:
        # Normal mode: use env vars or defaults
        max_round = int(os.environ.get('MAX_ROUNDS', '2000'))
        max_stage = int(os.environ.get('MAX_STAGES', '1'))
        num_generations = int(os.environ.get('NUM_GENERATIONS', '8'))
        num_transplant_trees = int(os.environ.get('NUM_TRANSPLANT_TREES', '0'))
        num_train_samples = int(os.environ.get('NUM_TRAIN_SAMPLES', '8'))
        dtype = 'float32'

    # Rollout sharing config
    rollout_publish_frequency = os.environ.get('ROLLOUT_PUBLISH_FREQUENCY', 'stage')
    rollout_cleanup_enabled = os.environ.get('ROLLOUT_CLEANUP_ENABLED', 'False').lower() == 'true'
    rollout_keep_last_n_rounds = int(os.environ.get('ROLLOUT_KEEP_LAST_N_ROUNDS', '10'))
    rollout_archive_old = os.environ.get('ROLLOUT_ARCHIVE_OLD', 'False').lower() == 'true'

    # Paths
    log_dir = f"{gdrive_path}/experiments/{experiment_name}/logs/{node_id}"

    # =======================
    # 1a. Setup Real-time Log Streaming to Google Drive
    # =======================
    log_flush_interval = float(os.environ.get('LOG_FLUSH_INTERVAL', '30.0'))
    log_streamer = setup_log_streaming(
        gdrive_path=gdrive_path,
        experiment_name=experiment_name,
        node_id=node_id,
        flush_interval=log_flush_interval
    )

    # =======================
    # 1b. Setup Progress Tracking
    # =======================
    progress_tracker = ProgressTracker(
        gdrive_path=gdrive_path,
        experiment_name=experiment_name,
        node_id=node_id
    )

    get_logger().info("="*60)
    get_logger().info("Starting RL Swarm (Google Drive Mode)")
    get_logger().info("="*60)
    get_logger().info(f"Experiment: {experiment_name}")
    get_logger().info(f"Node Role: {node_role}")
    get_logger().info(f"Node ID: {node_id}")
    get_logger().info(f"Model: {model_name}")
    get_logger().info(f"GDrive Path: {gdrive_path}")
    get_logger().info(f"Rollout Frequency: {rollout_publish_frequency}")
    get_logger().info(f"Training Config: I={num_train_samples}, J={num_transplant_trees}, G={num_generations}")
    get_logger().info(f"Max Rounds: {max_round}")
    get_logger().info("="*60)

    # =======================
    # 2. Create Rollout Sharing
    # =======================
    retention_config = {
        'cleanup_enabled': rollout_cleanup_enabled,
        'keep_last_n_rounds': rollout_keep_last_n_rounds,
        'archive_old_rollouts': rollout_archive_old,
        'archive_path': f"{gdrive_path}/archives/{experiment_name}/"
    }

    rollout_sharing = GDriveRolloutSharing(
        gdrive_path=gdrive_path,
        experiment_name=experiment_name,
        publish_frequency=rollout_publish_frequency,
        retention_config=retention_config
    )

    get_logger().info(f"✓ Created rollout sharing (cleanup={rollout_cleanup_enabled})")

    # =======================
    # 3. Create Communication Backend
    # =======================
    Communication.set_backend(GDriveCommunicationBackend)

    communication = GDriveCommunicationBackend(
        gdrive_rollout_sharing=rollout_sharing,
        node_id=node_id,
        experiment_name=experiment_name,
        rollout_publish_frequency=rollout_publish_frequency,
        fetch_max_peers=10,
        fetch_timeout_seconds=30,
        cache_rollouts=True
    )

    get_logger().info("✓ Created GDrive communication backend")

    # =======================
    # 4. Create Game State
    # =======================
    game_state = GameState(round=0, stage=0)
    get_logger().info("✓ Created game state")

    # =======================
    # 5. Create Reward Manager
    # =======================
    rg_rewards = RGRewards()
    round_reward_fn_store = RoundRewardFnStore(
        num_stages=max_stage,
        reward_fns=[rg_rewards]
    )
    reward_fn_store = RewardFnStore(
        max_rounds=max_round,
        reward_fn_stores=[round_reward_fn_store]
    )
    reward_manager = DefaultRewardManager(reward_fn_store=reward_fn_store)
    get_logger().info("✓ Created reward manager")

    # =======================
    # 6. Load Model
    # =======================
    get_logger().info(f"Loading model: {model_name}...")
    model = AutoModelForCausalLM.from_pretrained(model_name)

    # Explicitly place model on GPU for multi-process sharing
    # (using manual .to() instead of device_map allows multiple processes on same GPU)
    import torch
    if torch.cuda.is_available():
        model = model.to('cuda:0')
        get_logger().info(f"✓ Model placed on GPU (CUDA available)")
    else:
        get_logger().info("✓ Model on CPU (no CUDA)")

    get_logger().info("✓ Model loaded")

    # =======================
    # 7. Create Trainer
    # =======================
    trainer_config = GRPOTrainerConfig(
        dtype=dtype,
        epsilon=0.2,
        epsilon_high=0.28,
        num_generations=num_generations
    )

    trainer = GRPOTrainerModule(
        models=[model],
        config=trainer_config,
        log_dir=log_dir
    )

    # Patch GPT-2 tokenizer for compatibility with GenRL (completion model fixes)
    tokenizer = trainer.processing_class

    # Fix 1: Add chat template (GPT-2 doesn't have one by default)
    if not hasattr(tokenizer, 'chat_template') or tokenizer.chat_template is None:
        tokenizer.chat_template = (
            "{% for message in messages %}"
            "{{ message['content'] }}"
            "{% if not loop.last %}\n\n{% endif %}"
            "{% endfor %}"
        )
        get_logger().info("✓ Added chat template to tokenizer")

    # Fix 2: Add padding token (GPT-2 doesn't have one by default)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        get_logger().info(f"✓ Set pad_token = eos_token ({tokenizer.eos_token})")

    get_logger().info("✓ Created trainer")

    # =======================
    # 8. Create Data Manager
    # =======================
    data_manager = ReasoningGymDataManager(
        yaml_config_path="rgym_exp/src/datasets.yaml",
        num_train_samples=num_train_samples,
        num_evaluation_samples=0,
        num_generations=num_generations,
        system_prompt_id='default',
        seed=seed,
        num_transplant_trees=num_transplant_trees
    )
    get_logger().info("✓ Created data manager")

    # =======================
    # 9. Create Coordinator (all nodes need it to poll state)
    # =======================
    coordinator = GDriveSwarmCoordinator(
        gdrive_path=f"{gdrive_path}/experiments/{experiment_name}",
        node_role=node_role,
        round_check_interval=30
    )

    if node_role == 'coordinator':
        get_logger().info("✓ Created GDrive coordinator (will manage rounds)")
    else:
        get_logger().info("✓ Created GDrive coordinator (read-only, will poll state)")

    # =======================
    # 10. Create Game Manager
    # =======================
    game_manager = SwarmGameManager(
        coordinator=coordinator,
        max_stage=max_stage,
        max_round=max_round,
        game_state=game_state,
        reward_manager=reward_manager,
        trainer=trainer,
        data_manager=data_manager,
        communication=communication,
        role_manager=None,
        run_mode="train_and_evaluate",
        log_dir=log_dir,
        hf_token=hf_token,
        hf_push_frequency=20
    )

    get_logger().info("✓ Created game manager")
    get_logger().info("="*60)

    # =======================
    # 11. Run Game (or Coordinator Loop)
    # =======================
    try:
        if node_role == 'coordinator':
            get_logger().info("Starting coordinator loop (non-training)...")
            get_logger().info("="*60)
            game_manager.run_coordinator_loop()
            progress_tracker.log_training_complete(max_round)
        else:
            get_logger().info("Starting training...")
            get_logger().info("="*60)
            game_manager.run_game()
            progress_tracker.log_training_complete(max_round)
    except Exception as e:
        get_logger().error(f"Training failed: {e}")
        progress_tracker.log_error('training_failure', str(e))
        raise
    finally:
        # Ensure logs are flushed before exit
        get_logger().info("="*60)
        get_logger().info("Training complete. Flushing logs...")
        log_streamer.close()
        get_logger().info("="*60)


if __name__ == "__main__":
    main()
