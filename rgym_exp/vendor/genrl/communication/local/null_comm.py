from typing import Any, Dict, Sequence

from rgym_exp.vendor.genrl.communication.communication import Communication


class NullCommunicationBackend(Communication):
    """
    Mock backend for single agent, on-device usecases
    """

    def __init__(self, world_sizes: Sequence[tuple[str, int]] | None = None):
        self._mesh = None

    def all_gather_object(self, obj: Any, *args, **kwargs) -> Dict[str | int, Any]:
        out = [obj]
        return {index: value for index, value in enumerate(out)}

    def get_id(self):
        return 0
