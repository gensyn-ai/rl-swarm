import os
import time
import hydra
from genrl.communication.communication import Communication
from genrl.communication.hivemind.hivemind_backend import (
    HivemindBackend,
    HivemindRendezvouz,
)
from hydra.utils import instantiate
from omegaconf import DictConfig, OmegaConf
from genrl.logging_utils.global_defs import get_logger
from code_gen_exp.src.utils.omega_gpu_resolver import (
    gpu_model_choice_resolver,
)  # necessary for gpu_model_choice resolver in hydra config

import logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("hivemind").setLevel(logging.CRITICAL)

@hydra.main(version_base=None)
def main(cfg: DictConfig):
    is_master = True
    HivemindRendezvouz.init(is_master=is_master)

    max_retries = 3
    for i in range(max_retries):
        try:
            game_manager = instantiate(cfg.game_manager)
            break  
        except Exception as e:
            if "not a local folder and is not a valid model identifier" in str(e):
                if i < max_retries - 1:
                    get_logger().warning("If the repo you requested exists, Hugging Face servers may be temporarily unavailable or rate-limited. "
                                    "Please retry until the Hugging Face download completes successfully.")
                    time.sleep(5)
                else:
                    raise
            else:
                # raise if it's a different error
                raise
    game_manager.run_game()


if __name__ == "__main__":
    os.environ["HYDRA_FULL_ERROR"] = "1"
    Communication.set_backend(HivemindBackend)
    main()
