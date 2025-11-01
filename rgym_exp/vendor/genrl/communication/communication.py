import abc
import inspect
from dataclasses import dataclass
from typing import Any, Dict, Type


class Communication(abc.ABC):

    _BACKEND_CLS: Type | None = None

    @abc.abstractmethod
    def all_gather_object(self, obj: Any, *args, **kwargs) -> Dict[str | int, Any]:
        pass

    @abc.abstractmethod
    def get_id(self) -> int | str:
        pass

    @classmethod
    def set_backend(cls, backend_cls) -> None:
        if not issubclass(backend_cls, cls):
            raise RuntimeError(f"{backend_cls} must be subclass of {cls}.")
        cls._BACKEND_CLS = backend_cls

    @classmethod
    def create(cls, **kwargs):
        if cls._BACKEND_CLS is None:
            raise RuntimeError(
                "Communication backend class is not set by the launcher."
            )
        signature = inspect.signature(cls._BACKEND_CLS.__init__)
        params = {
            name: kwargs.get(name, param.default)
            for name, param in signature.parameters.items()
            if name != "self"
        }
        return cls._BACKEND_CLS(**params)


@dataclass
class Payload(dict):
    """
    Provides a template for organizing objects being communicated throughout the swarm.
    """

    world_state: Any = None
    actions: Any = None
    metadata: Any = None

    # Methods for emulating a mapping container object
    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)
