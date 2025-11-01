from typing import Any, Optional, List

import torch
from rgym_exp.vendor.genrl.data import DataManager
from rgym_exp.vendor.genrl.logging_utils.global_defs import get_logger
from rgym_exp.vendor.genrl.logging_utils.ml_logger import LoggerMixin
from rgym_exp.vendor.genrl.rewards import RewardManager
from rgym_exp.vendor.genrl.state import GameState
from rgym_exp.vendor.genrl.trainer.grpo_trainer import GRPOLanguageTrainerModule



class GRPOTrainerModule(GRPOLanguageTrainerModule, LoggerMixin):
    """
    Trainer for the Group Relative Policy Optimization (GRPO) method.
    Implements the TrainerModule interface defined in base_trainer.py.
    """

    def __init__(self, models: List[Any], **kwargs):
        """
        Initialize the GRPO trainer module.

        Args:
            models: List containing the model to be trained.
            **kwargs: Additional arguments for configuration.
        """
        super().__init__(models, **kwargs)