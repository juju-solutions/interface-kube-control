from typing import Union
from dataclasses import dataclass
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


@dataclass
class Taint(_ModelObject):
    """Definition of a Node Taint."""

    key: str
    value: str
    effect: Effect

    def __str__(self):
        """Encode a taint object to a string."""
        return f"{self.key}={self.value}:{self.effect.name}"

    @classmethod
    def decode(cls, source: str):
        """Decode a taint object from a string."""
        key, tail = source.split("=", 1)
        value, effect = tail.split(":", 1)
        return cls(key, value, Effect[effect])


@dataclass
class Label(_ModelObject):
    """Definition of a Label."""

    key: str
    value: str

    def __str__(self):
        """Encode a label object to a string."""
        return f"{self.key}={self.value}"

    @classmethod
    def decode(cls, source: str):
        """Decode a label object from a string."""
        key, value = source.split("=", 1)
        return cls(key, value)
