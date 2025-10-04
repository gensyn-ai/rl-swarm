import os
import uuid

import hydra
from genrl.communication.communication import Communication
from genrl.communication.hivemind.hivemind_backend import (
    HivemindBackend,
    HivemindRendezvouz,
)
from genrl.logging_utils.global_defs import get_logger
from hydra.utils import instantiate
from omegaconf import DictConfig, OmegaConf

from rgym_exp.src.utils.omega_gpu_resolver import (
    gpu_model_choice_resolver,
)  # necessary for gpu_model_choice resolver in hydra config


@hydra.main(version_base=None)
def main(cfg: DictConfig):
    # Check if running in GDrive mode
    gdrive_mode = cfg.get('gdrive', {}).get('base_path') is not None

    if gdrive_mode:
        get_logger().info("Running in Google Drive mode (no Hivemind)")

        # Initialize GDrive communication backend
        from rgym_exp.src.gdrive_rollout_sharing import GDriveRolloutSharing
        from rgym_exp.communication.gdrive_backend import GDriveCommunicationBackend

        gdrive_base_path = cfg.gdrive.base_path
        experiment_name = os.environ.get('EXPERIMENT_NAME', 'default')
        node_id = os.environ.get('NODE_ID', str(uuid.uuid4())[:8])

        # Get retention config from config file
        retention_config = {
            'cleanup_enabled': cfg.communication.get('rollout_retention', {}).get('cleanup_enabled', False),
            'keep_last_n_rounds': cfg.communication.get('rollout_retention', {}).get('keep_last_n_rounds', 5),
            'archive_old_rollouts': cfg.communication.get('rollout_retention', {}).get('archive_old_rollouts', False),
            'archive_path': cfg.communication.get('rollout_retention', {}).get('archive_path',
                f"{gdrive_base_path}/archives/{experiment_name}/")
        }

        # Create rollout sharing instance
        rollout_sharing = GDriveRolloutSharing(
            gdrive_path=gdrive_base_path,
            experiment_name=experiment_name,
            publish_frequency=cfg.communication.get('rollout_publish_frequency', 'stage'),
            retention_config=retention_config
        )

        # Set communication backend to GDrive
        Communication.set_backend(GDriveCommunicationBackend)

        # Store in config for game_manager initialization
        cfg.communication.gdrive_rollout_sharing = rollout_sharing
        cfg.communication.node_id = node_id
        cfg.communication.experiment_name = experiment_name

        get_logger().info(f"Node ID: {node_id}")
        get_logger().info(f"Rollout publish frequency: {cfg.communication.get('rollout_publish_frequency', 'stage')}")
        get_logger().info(f"Rollout retention: cleanup={retention_config['cleanup_enabled']}, keep_last_n={retention_config['keep_last_n_rounds']}")

    else:
        # Original Hivemind mode
        get_logger().info("Running in Hivemind mode")
        Communication.set_backend(HivemindBackend)
        is_master = False
        HivemindRendezvouz.init(is_master=is_master)

    game_manager = instantiate(cfg.game_manager)
    game_manager.run_game()


if __name__ == "__main__":
    os.environ["HYDRA_FULL_ERROR"] = "1"
    Communication.set_backend(HivemindBackend)
    main()
