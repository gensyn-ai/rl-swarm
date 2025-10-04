import os

import hydra
from genrl.communication.communication import Communication
from genrl.communication.hivemind.hivemind_backend import (
    HivemindBackend,
    HivemindRendezvouz,
)
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
        get_logger().info("Running in Google Drive mode (no blockchain)")

        # Initialize GDrive discovery if enabled
        if cfg.communications.get('use_gdrive_discovery', False):
            from rgym_exp.src.gdrive_discovery import GDrivePeerDiscovery

            discovery_path = cfg.communications.discovery_path
            get_logger().info(f"Initializing peer discovery at {discovery_path}")

            discovery = GDrivePeerDiscovery(discovery_path)

            # Get peer ID from communication backend
            # We need to initialize HivemindRendezvouz first
            is_master = False
            HivemindRendezvouz.init(is_master=is_master)

            # Get our peer ID and publish multiaddr
            # Note: We'll publish after game_manager is created when we have the actual multiaddr
            get_logger().info("GDrive peer discovery enabled")

            # Discover existing peers
            discovered_peers = discovery.discover_peers(max_peers=10)
            if discovered_peers:
                cfg.communications.initial_peers = discovered_peers
                get_logger().info(f"Discovered {len(discovered_peers)} peers via Google Drive")
        else:
            is_master = False
            HivemindRendezvouz.init(is_master=is_master)
    else:
        is_master = False
        HivemindRendezvouz.init(is_master=is_master)

    game_manager = instantiate(cfg.game_manager)
    game_manager.run_game()


if __name__ == "__main__":
    os.environ["HYDRA_FULL_ERROR"] = "1"
    Communication.set_backend(HivemindBackend)
    main()
