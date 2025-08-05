import random

import torch
from omegaconf import OmegaConf


def get_gpu_vram():
    """Returns the total VRAM of the first available GPU in GiB."""
    if not torch.cuda.is_available():
        return 0

    total_memory = torch.cuda.get_device_properties(0).total_memory
    return total_memory / (1024**3)  # Convert bytes to GiB


def gpu_model_choice_resolver(large_model_pool, small_model_pool):
    """Selects a model from the large or small pool based on VRAM."""
    vram = get_gpu_vram()
    if vram >= 40:
        model_pool = large_model_pool
    else:
        model_pool = small_model_pool
    return random.choice(model_pool)


OmegaConf.register_new_resolver("gpu_model_choice", gpu_model_choice_resolver)
