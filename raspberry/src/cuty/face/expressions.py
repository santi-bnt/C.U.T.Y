"""Serializable robot expression events."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite


class Expression(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    HAPPY = "happy"
    EXCITED = "excited"
    CONFUSED = "confused"
    SAD = "sad"
    SLEEPY = "sleepy"
    SURPRISED = "surprised"


@dataclass(frozen=True)
class ExpressionEvent:
    expression: Expression
    intensity: float = 1.0
    type: str = "expression"

    def __post_init__(self) -> None:
        if not isinstance(self.expression, Expression):
            raise ValueError("Invalid expression")
        if not isinstance(self.intensity, (int, float)) or isinstance(self.intensity, bool):
            raise ValueError("Intensity must be a number from 0 to 1")
        if not isfinite(self.intensity) or not 0 <= self.intensity <= 1:
            raise ValueError("Intensity must be a number from 0 to 1")

    def as_dict(self) -> dict[str, str | float]:
        return {"type": self.type, "expression": self.expression.value, "intensity": float(self.intensity)}
