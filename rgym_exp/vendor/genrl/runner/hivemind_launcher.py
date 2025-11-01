import logging
import os
import socket

import hydra
from hydra.utils import instantiate
from omegaconf import DictConfig, OmegaConf

from rgym_exp.vendor.genrl.communication.communication import Communication
from rgym_exp.vendor.genrl.communication.hivemind.hivemind_backend import (
    HivemindBackend,
    HivemindRendezvouz,
)
from rgym_exp.vendor.genrl.logging_utils.global_defs import get_logger


@hydra.main(version_base=None)
def main(cfg: DictConfig):
    master_addr = os.environ["MASTER_ADDR"]
    world_size = os.environ.get("HIVEMIND_WORLD_SIZE", 1)
    node_address = socket.gethostname()
    full_node_address = socket.getfqdn()
    is_master = full_node_address == master_addr
    HivemindRendezvouz.init(is_master=is_master)

    format_msg = f"[{node_address}] %(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=format_msg)
    formatter = logging.Formatter(format_msg)
    log_dir = cfg.log_dir
    file_handler = logging.FileHandler(
        os.path.join(log_dir, f"training_{node_address}.log")
    )
    file_handler.setFormatter(formatter)
    # TODO(jkolehm): have logging level specified in the hydra config.
    _LOG = get_logger()
    _LOG.addHandler(file_handler)

    if is_master:
        _LOG.info(OmegaConf.to_yaml(cfg))
        _LOG.info(
            f"Using communication backend: hivemind with {world_size} minimum workers."
        )
    game_manager = instantiate(cfg.game_manager)
    game_manager.run_game()
    _LOG.info(f"Finished training on node: {node_address}.")


if __name__ == "__main__":
    os.environ["HYDRA_FULL_ERROR"] = "1"
    Communication.set_backend(HivemindBackend)
    main()
