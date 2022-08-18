from typing import Union
from enum import Enum, auto


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

    def __init__(self, key: str, value: str, effect: Effect) -> None:
        self.key = key
        self.value = value
        self.effect = effect

    def __str__(self):
        """Encode a taint object to a string."""
        return f"{self.key}={self.value}:{self.effect.name}"

    def __eq__(self, __o: object) -> bool:
        return (self.key, self.value, self.effect) == (__o.key, __o.value, __o.effect)

    @classmethod
    def decode(cls, source: str):
        """Decode a taint object from a string."""
        key, tail = source.split("=", 1)
        value, effect = tail.split(":", 1)
        return cls(key, value, Effect[effect])


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
        key, value = source.split("=", 1)
        return cls(key, value)
