from typing import Union, Optional
from enum import Enum, auto


class DecodeError(Exception):
    pass


class Effect(Enum):
    """Enumerates possible taint effects."""

    NoSchedule = auto()
    PreferNoSchedule = auto()
    NoExecute = auto()


class _ModelObject:
    @classmethod
    def valid(cls, source: Union[str, "_ModelObject"]) -> "_ModelObject":
        if isinstance(source, str):
            source = cls.decode(source)
        return isinstance(source, cls)


class Taint(_ModelObject):
    """Definition of a Node Taint."""

    def __init__(self, key: str, value: Optional[str], effect: Effect) -> None:
        self.key = key
        self.value = value
        self.effect = effect

    def __str__(self):
        """Encode a taint object to a string."""
        key_value = "=".join(filter(None, (self.key, self.value)))
        return f"{key_value}:{self.effect.name}"

    def __eq__(self, __o: object) -> bool:
        return (self.key, self.value, self.effect) == (__o.key, __o.value, __o.effect)

    @classmethod
    def decode(cls, source: str):
        """Decode a taint object from a string."""
        try:
            key_value, effect = source.split(":")
            key, *value = key_value.split("=", 1)
            effect_value = Effect[effect]
        except ValueError as ex:
            raise DecodeError("Taint must contain a single ':'") from ex
        except KeyError as ex:
            options = ",".join([_.name for _ in Effect])
            raise DecodeError(f"Taint effect must be {options}") from ex
        return cls(key, next(iter(value), None), effect_value)


class Label(_ModelObject):
    """Definition of a Label."""

    def __init__(self, key: str, value: str) -> None:
        self.key = key
        self.value = value

    def __eq__(self, __o: object) -> bool:
        return (self.key, self.value) == (__o.key, __o.value)

    def __str__(self):
        """Encode a label object to a string."""
        return f"{self.key}={self.value}"

    @classmethod
    def decode(cls, source: str):
        """Decode a label object from a string."""
        try:
            key, value = source.split("=")
        except ValueError as ex:
            raise DecodeError("Label must contain a single '='") from ex
        return cls(key, value)
