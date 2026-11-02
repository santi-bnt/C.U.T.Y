"""Expression dispatch and state baseline selection."""

from __future__ import annotations

import logging
from typing import Protocol

from cuty.brain.states import State
from cuty.face.expressions import Expression, ExpressionEvent


class ExpressionSink(Protocol):
    def set_expression(self, expression: Expression, intensity: float = 1.0) -> None: ...


class ConsoleExpressionSink:
    def set_expression(self, expression: Expression, intensity: float = 1.0) -> None:
        event = ExpressionEvent(expression, intensity)
        logging.getLogger("CUTY FACE").info("%s intensity=%.1f", event.expression.value.upper(), event.intensity)


_BASELINE = {
    State.IDLE: Expression.IDLE,
    State.LISTENING: Expression.LISTENING,
    State.THINKING: Expression.THINKING,
    State.SPEAKING: Expression.SPEAKING,
}


class ExpressionController:
    def __init__(self, sink: ExpressionSink) -> None:
        self.sink = sink
        self._emotion: ExpressionEvent | None = None

    def on_state(self, state: State) -> None:
        if state in {State.IDLE, State.ERROR}:
            self._emotion = None
        if state in _BASELINE:
            event = self._emotion or ExpressionEvent(_BASELINE[state])
            self.sink.set_expression(event.expression, event.intensity)

    def set_emotion(self, expression: Expression, intensity: float) -> ExpressionEvent:
        if expression in _BASELINE.values():
            raise ValueError("A model cannot set a baseline state expression")
        event = ExpressionEvent(expression, intensity)
        self._emotion = event
        self.sink.set_expression(event.expression, event.intensity)
        return event
