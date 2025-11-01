import logging
import os
from dataclasses import dataclass
from types import TracebackType
from typing import Optional, Type

import hydra
import torch
import torch.distributed
from hydra.utils import instantiate
from omegaconf import DictConfig, OmegaConf
from torch.distributed.elastic.multiprocessing.errors import record

from rgym_exp.vendor.genrl.communication.communication import Communication
from rgym_exp.vendor.genrl.communication.distributed.torch_comm import TorchBackend
from rgym_exp.vendor.genrl.logging_utils.global_defs import get_logger


@dataclass
class _DistributedContext:
    backend: str

    def __enter__(self) -> None:
        torch.distributed.init_process_group(backend=self.backend)

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        torch.distributed.destroy_process_group()


@record
def _main(cfg: DictConfig):
    local_rank = int(os.environ["LOCAL_RANK"])
    world_size = int(os.environ["WORLD_SIZE"])
    if torch.cuda.is_available():
        backend = torch.distributed.Backend.NCCL
    else:
        backend = torch.distributed.Backend.GLOO

    log_dir = cfg.log_dir

    with _DistributedContext(backend):
        rank = torch.distributed.get_rank()
        if rank == 0:
            # Assume log_dir is in shared volume.
            os.makedirs(log_dir, exist_ok=True)
        torch.distributed.barrier()
        format_msg = f"[{rank}] %(asctime)s %(levelname)s: %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=format_msg)
        formatter = logging.Formatter(format_msg)
        file_handler = logging.FileHandler(
            os.path.join(log_dir, f"training_{rank}.log")
        )
        file_handler.setFormatter(formatter)
        # TODO(jkolehm): have logging level specified in the hydra config.
        _LOG = get_logger()
        _LOG.addHandler(file_handler)

        if rank == 0:
            _LOG.info(OmegaConf.to_yaml(cfg))
            _LOG.info(
                f"Using communication backend: {backend} with {world_size} workers."
            )
        _LOG.debug(
            f"Launching distributed training with {local_rank=} {rank=} {world_size=}."
        )
        game_manager = instantiate(cfg.game_manager)
        game_manager.rank = rank
        game_manager.run_game()
        _LOG.debug(f"Finished training on {local_rank=} {rank=}.")


@hydra.main(version_base=None)
def main(cfg: DictConfig) -> None:
    # Set error logging to error.log in the specified log directory.
    log_dir = cfg.log_dir
    os.environ["TORCHELASTIC_ERROR_FILE"] = os.path.join(log_dir, "error.log")
    _main(cfg)


if __name__ == "__main__":
    os.environ["HYDRA_FULL_ERROR"] = "1"
    Communication.set_backend(TorchBackend)
    main()
