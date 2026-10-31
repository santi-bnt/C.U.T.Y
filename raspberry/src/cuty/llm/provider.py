"""Small provider contract used by the conversation service and test fakes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class ProviderError(RuntimeError):
    pass


class EventKind(str, Enum):
    AUDIO = "audio"
    TRANSCRIPT = "transcript"
    INPUT_TRANSCRIPT = "input_transcript"
    WEB_SEARCH = "web_search"
    DONE = "done"
    OTHER = "other"


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    name: str
    arguments: str


@dataclass(frozen=True)
class WebSource:
    title: str
    url: str
    snippet: str = ""


@dataclass(frozen=True)
class AIEvent:
    kind: EventKind
    audio: bytes = b""
    transcript: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    search_queries: tuple[str, ...] = ()
    sources: tuple[WebSource, ...] = ()


class AIProvider(Protocol):
    async def connect(self) -> None: ...
    async def close(self) -> None: ...
    async def start_turn(self) -> None: ...
    async def send_audio(self, pcm16: bytes) -> None: ...
    async def finish_input(self) -> None: ...
    async def receive(self) -> AIEvent: ...
    async def submit_tool_result(self, call_id: str, output: str) -> None: ...
    async def continue_response(self) -> None: ...
