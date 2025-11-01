from enum import Enum
from typing import Dict, Union

import wandb
from torch.utils import tensorboard

from rgym_exp.vendor.genrl.logging_utils.global_defs import get_logger


class LogTypes(Enum):
    NONE = "none"
    TENSORBOARD = "tensorboard"
    WANDB = "wandb"


class LoggerMixin:
    def __init__(self):
        self.logging_dir = None
        self.tracker = None
        self.log_with = None

    def init_tracker(self, logging_dir: str, log_with: LogTypes = LogTypes.TENSORBOARD):
        self.logging_dir = logging_dir
        try:
            self.log_with = LogTypes(log_with)
        except ValueError:
            self.log_with = LogTypes.NONE

        if self.log_with == LogTypes.TENSORBOARD:
            self.tracker = tensorboard.SummaryWriter(self.logging_dir)
        elif self.log_with == LogTypes.WANDB:
            self.tracker = wandb.init(
                project="genrl", dir=logging_dir, mode="offline"
            )
        else:
            self.tracker = get_logger()
            self.tracker.info(
                f"Invalid log type: {log_with}. Default to terminal logging"
            )

    def log(
        self,
        metrics: Dict[str, Union[int, float, str, Dict[str, Union[int, float]]]],
        global_step: int,
    ):
        if self.log_with == LogTypes.TENSORBOARD:
            for k, v in metrics.items():
                if isinstance(v, (int, float)):
                    self.tracker.add_scalar(k, v, global_step=global_step)
                elif isinstance(v, str):
                    self.tracker.add_text(k, v, global_step=global_step)
                elif isinstance(v, dict):
                    self.tracker.add_scalars(k, v, global_step=global_step)
            self.tracker.flush()
        elif self.log_with == LogTypes.WANDB:
            self.tracker.log(metrics, step=global_step)
        else:
            self.tracker.info(metrics)

    def cleanup_trackers(self):
        if self.log_with == LogTypes.TENSORBOARD:
            self.tracker.close()
        elif self.log_with == LogTypes.WANDB:
            self.tracker.finish()


class ImageLoggerMixin(LoggerMixin):
    def log_images(self, images, prompts, global_step):
        result = {}
        for image, prompt in zip(images, prompts):
            result[f"{prompt}"] = image

        for k, v in result.items():
            if self.log_with == LogTypes.TENSORBOARD:
                self.tracker.add_image(k, v, global_step=global_step)
                self.tracker.flush()
            elif self.log_with == LogTypes.WANDB:
                self.tracker.log({k: wandb.Image(v, caption=k)}, step=global_step)
