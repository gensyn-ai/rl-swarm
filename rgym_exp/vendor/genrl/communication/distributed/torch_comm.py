from typing import Any, Dict, Sequence

import torch.distributed as dist

from rgym_exp.vendor.genrl.communication.communication import Communication


class TorchBackend(Communication):
    def __init__(self, world_sizes: Sequence[tuple[str, int]] | None = None):
        if world_sizes is not None:
            names_, world_sizes_ = zip(*world_sizes)
            self._mesh = dist.init_device_mesh(
                "cuda", world_sizes_, mesh_dim_names=names_
            )
        else:
            self._mesh = None

    def all_gather_object(self, obj: Any, *args, **kwargs) -> Dict[str | int, Any]:
        if "name" in kwargs:
            group = self._mesh.get_group(mesh_dim=kwargs.get("name"))
        else:
            group = None
        out = [None] * dist.get_world_size(group=group)
        dist.all_gather_object(
            out,
            obj,
            group=group,
        )
        return {index: value for index, value in enumerate(out)}

    def get_id(self):
        return dist.get_rank()
