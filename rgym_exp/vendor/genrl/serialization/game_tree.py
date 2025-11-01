import struct  # Added for float serialization
import sys
from types import NoneType
from typing import Any, Dict, List, Tuple, Type

from rgym_exp.vendor.genrl.communication.communication import Payload
from rgym_exp.vendor.genrl.state import WorldState


class ObjType:
    LIST = 1
    DICT = 2
    STRING = 3
    INTEGER = 4
    FLOAT = 5
    BOOLEAN = 6
    PAYLOAD = 7
    WORLD_STATE = 8
    NONE = 9


class Serializer:
    _SERIALIZATION_METHOD = {}
    _DESERIALIZATION_METHOD = {}

    @classmethod
    def from_bytes(cls, obj_type: ObjType):
        if obj_type not in cls._DESERIALIZATION_METHOD:
            raise RuntimeError(
                f"Unsupported type: {obj_type}; supported types are {list(cls._DESERIALIZATION_METHOD.keys())}."
            )
        return cls._DESERIALIZATION_METHOD[obj_type]

    @classmethod
    def to_bytes(cls, obj_type: Type):
        if obj_type not in cls._SERIALIZATION_METHOD:
            raise RuntimeError(
                f"Unsupported type: {obj_type}; supported types are {list(cls._SERIALIZATION_METHOD.keys())}."
            )
        return cls._SERIALIZATION_METHOD[obj_type]

    @classmethod
    def register_deserializer(cls, obj_type: ObjType):
        def wrapper(fn):
            cls._DESERIALIZATION_METHOD[obj_type] = fn
            return fn

        return wrapper

    @classmethod
    def register_serializer(cls, obj_type: Type):
        def wrapper(fn):
            cls._SERIALIZATION_METHOD[obj_type] = fn
            return fn

        return wrapper


def _from_bytes(b: bytes, i: int) -> Tuple[Any, int]:
    obj_type = int.from_bytes(b[i : (i + 8)], byteorder="big", signed=False)
    i += 8
    return Serializer.from_bytes(obj_type)(b, i)


@Serializer.register_deserializer(ObjType.INTEGER)
def int_from_bytes(b: bytes, i: int) -> Tuple[int, int]:
    n_bytes = int.from_bytes(b[i : (i + 8)], byteorder="big", signed=False)
    i += 8
    value = int.from_bytes(b[i : (i + n_bytes)], byteorder="big", signed=True)
    return value, i + n_bytes


@Serializer.register_deserializer(ObjType.FLOAT)
def float_from_bytes(b: bytes, i: int) -> Tuple[float, int]:
    n_bytes = int.from_bytes(b[i : (i + 8)], byteorder="big", signed=False)
    i += 8
    value_tuple = struct.unpack(">d", b[i : (i + n_bytes)])
    value = value_tuple[0]  # struct.unpack returns a tuple
    return value, i + n_bytes


@Serializer.register_deserializer(ObjType.STRING)
def string_from_bytes(b: bytes, i: int) -> Tuple[str, int]:
    n_bytes = int.from_bytes(b[i : (i + 8)], byteorder="big", signed=False)
    i += 8
    s = b[i : (i + n_bytes)].decode("utf-8")
    i += n_bytes
    return s, i


@Serializer.register_deserializer(ObjType.LIST)
def list_from_bytes(b: bytes, i: int) -> Tuple[List[Any], int]:
    n_items = int.from_bytes(b[i : (i + 8)], byteorder="big", signed=False)
    i += 8
    out = [None] * n_items

    for k in range(n_items):
        out[k], i = _from_bytes(b, i)
    return out, i


@Serializer.register_deserializer(ObjType.DICT)
def dict_from_bytes(b: bytes, i: int) -> Tuple[List[Any], int]:
    n_items = int.from_bytes(b[i : (i + 8)], byteorder="big", signed=False)
    i += 8
    out = {}
    for _ in range(n_items):
        key, i = _from_bytes(b, i)
        value, i = _from_bytes(b, i)
        out[key] = value
    return out, i


@Serializer.register_deserializer(ObjType.PAYLOAD)
def payload_from_bytes(b: bytes, i: int) -> Tuple[List[Any], int]:
    world_state, i = _from_bytes(b, i)
    actions, i = _from_bytes(b, i)
    metadata, i = _from_bytes(b, i)
    return Payload(world_state=world_state, actions=actions, metadata=metadata), i


@Serializer.register_deserializer(ObjType.WORLD_STATE)
def world_state_from_bytes(b: bytes, i: int) -> Tuple[WorldState, int]:
    environment_states, i = _from_bytes(b, i)
    opponent_states, i = _from_bytes(b, i)
    personal_states, i = _from_bytes(b, i)
    return (
        WorldState(
            environment_states=environment_states,
            opponent_states=opponent_states,
            personal_states=personal_states,
        ),
        i,
    )


@Serializer.register_deserializer(ObjType.NONE)
def none_from_bytes(b: bytes, i: int) -> Tuple[List[Any], int]:
    return None, i


@Serializer.register_deserializer(ObjType.BOOLEAN)
def boolean_from_bytes(b: bytes, i: int) -> Tuple[List[Any], int]:
    return b[i] == b"0", i + 1


@Serializer.register_serializer(bool)
def boolean_to_bytes(obj: bool) -> bytes:
    type_bytes = ObjType.BOOLEAN.to_bytes(length=8, byteorder="big", signed=False)
    bool_bytes = b"0" if not obj else b"1"
    return type_bytes + bool_bytes


@Serializer.register_serializer(NoneType)
def none_to_bytes(obj: None) -> bytes:
    return ObjType.NONE.to_bytes(length=8, byteorder="big", signed=False)


@Serializer.register_serializer(Payload)
def payload_to_bytes(obj: Payload) -> bytes:
    type_bytes = ObjType.PAYLOAD.to_bytes(length=8, byteorder="big", signed=False)
    world_state_bytes = to_bytes(obj.world_state)
    actions_bytes = to_bytes(obj.actions)
    metadata_bytes = to_bytes(obj.metadata)
    return type_bytes + world_state_bytes + actions_bytes + metadata_bytes


@Serializer.register_serializer(WorldState)
def world_state_to_bytes(obj: WorldState) -> bytes:
    type_bytes = ObjType.WORLD_STATE.to_bytes(length=8, byteorder="big", signed=False)
    environment_states_bytes = to_bytes(obj.environment_states)
    opponent_states_bytes = to_bytes(obj.opponent_states)
    personal_bytes = to_bytes(obj.personal_states)
    return (
        type_bytes + environment_states_bytes + opponent_states_bytes + personal_bytes
    )


@Serializer.register_serializer(int)
def int_to_bytes(obj: int) -> bytes:
    type_bytes = ObjType.INTEGER.to_bytes(length=8, byteorder="big", signed=False)
    byte_length = sys.getsizeof(obj)
    int_bytes = obj.to_bytes(length=byte_length, byteorder="big", signed=True)
    size_header = byte_length.to_bytes(length=8, byteorder="big", signed=False)
    return type_bytes + size_header + int_bytes


@Serializer.register_serializer(float)
def float_to_bytes(obj: float) -> bytes:
    type_bytes = ObjType.FLOAT.to_bytes(length=8, byteorder="big", signed=False)
    packed_float_bytes = struct.pack(">d", obj)
    byte_length = len(packed_float_bytes)  # This will be 8 for '>d'
    size_header = byte_length.to_bytes(length=8, byteorder="big", signed=False)
    return type_bytes + size_header + packed_float_bytes


@Serializer.register_serializer(str)
def string_to_bytes(obj: str) -> bytes:
    serialized_obj = obj.encode("utf-8")
    type_bytes = ObjType.STRING.to_bytes(length=8, byteorder="big", signed=False)
    len_bytes = len(serialized_obj).to_bytes(length=8, byteorder="big", signed=False)
    return type_bytes + len_bytes + serialized_obj


@Serializer.register_serializer(dict)
def dict_to_bytes(obj: Dict[Any, Any]) -> bytes:
    type_bytes = ObjType.DICT.to_bytes(length=8, byteorder="big", signed=False)
    len_bytes = len(obj).to_bytes(length=8, byteorder="big", signed=False)
    dict_bytes = []
    for key, value in obj.items():
        dict_bytes.append(to_bytes(key))
        dict_bytes.append(to_bytes(value))
    return type_bytes + len_bytes + b"".join(dict_bytes)


@Serializer.register_serializer(list)
def list_to_bytes(obj: List[Any]) -> bytes:
    type_bytes = ObjType.LIST.to_bytes(length=8, byteorder="big", signed=False)
    count_bytes = len(obj).to_bytes(length=8, byteorder="big", signed=False)
    header = type_bytes + count_bytes
    serialized_list = [to_bytes(x) for x in obj]
    return header + b"".join(serialized_list)


def to_bytes(obj: Any) -> bytes:
    return Serializer.to_bytes(type(obj))(obj)


def from_bytes(b: bytes) -> Any:
    return _from_bytes(b, 0)[0]
