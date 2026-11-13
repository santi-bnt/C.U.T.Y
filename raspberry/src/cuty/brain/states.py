"""Validated robot state transitions."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Callable


class State(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    MUSIC_PLAYING = "MUSIC_PLAYING"
    MUSIC_PAUSED = "MUSIC_PAUSED"
    ERROR = "ERROR"


_ALLOWED = {
    State.IDLE: {State.LISTENING, State.THINKING, State.MUSIC_PLAYING, State.MUSIC_PAUSED, State.ERROR},
    State.LISTENING: {State.THINKING, State.ERROR, State.IDLE},
    State.THINKING: {State.SPEAKING, State.IDLE, State.ERROR},
    State.SPEAKING: {State.IDLE, State.MUSIC_PLAYING, State.MUSIC_PAUSED, State.ERROR},
    State.MUSIC_PLAYING: {State.LISTENING, State.MUSIC_PAUSED, State.THINKING, State.IDLE, State.ERROR},
    State.MUSIC_PAUSED: {State.LISTENING, State.MUSIC_PLAYING, State.THINKING, State.IDLE, State.ERROR},
    State.ERROR: {State.IDLE},
}


class StateMachine:
    def __init__(self, on_change: Callable[[State], None] | None = None) -> None:
        self.current = State.IDLE
        self._on_change = on_change

    def set(self, next_state: State) -> None:
        if next_state == self.current:
            return
        if next_state not in _ALLOWED[self.current]:
            raise ValueError(f"Invalid state transition: {self.current.value} -> {next_state.value}")
        self.current = next_state
        logging.getLogger("CUTY").info("STATE -> %s", next_state.value)
        if self._on_change:
            self._on_change(next_state)
