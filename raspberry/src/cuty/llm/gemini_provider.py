"""Gemini Live native-audio adapter for the no-cost API tier."""

from __future__ import annotations

import asyncio
import json
import logging
from collections import deque
from datetime import datetime
from typing import Any, AsyncIterator
from urllib.parse import urlsplit

from google import genai
from google.genai import types

from cuty.llm.provider import AIEvent, EventKind, ProviderError, ToolCall, WebSource
from cuty.brain.personality import INSTRUCTIONS, WEB_INSTRUCTIONS
from cuty.face.expressions import Expression


_EMOTIONS = [e.value for e in Expression if e.value not in {"idle", "listening", "thinking", "speaking"}]
_CONFIG = {
    "response_modalities": ["AUDIO"],
    "system_instruction": INSTRUCTIONS + WEB_INSTRUCTIONS,
    "input_audio_transcription": {},
    "output_audio_transcription": {},
    # The CLI owns the turn boundaries (ENTER), so do not wait for server VAD.
    "realtime_input_config": {"automatic_activity_detection": {"disabled": True}},
    "tools": [{"function_declarations": [{
        "name": "set_expression",
        # Gemini 3.8 defaults to asynchronous calls. An expression-only turn
        # otherwise completes without speech after the silent function result.
        "behavior": "BLOCKING",
        "description": "Display a temporary emotion while C.U.T.Y responds.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "expression": {"type": "STRING", "enum": _EMOTIONS},
                "intensity": {"type": "NUMBER", "minimum": 0, "maximum": 1},
            },
            "required": ["expression", "intensity"],
        },
    }, {
        "name": "search_web",
        "behavior": "BLOCKING",
        "description": "Search public web pages for current information and return source links and excerpts.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"query": {"type": "STRING", "description": "A concise, targeted search query."}},
            "required": ["query"],
        },
    }]}],
}


class GeminiLiveProvider:
    def __init__(self, api_key: str, model: str = "gemini-3.8-live") -> None:
        self._api_key = api_key
        self._model = model
        self._client = genai.Client(api_key=api_key)
        self._manager: Any = None
        self._session: Any = None
        self._messages: AsyncIterator[types.LiveServerMessage] | None = None
        self._pending: deque[AIEvent] = deque()
        self._call_names: dict[str, str] = {}
        self._activity_started = False
        self._seen_queries: set[str] = set()
        self._seen_sources: set[str] = set()
        self._log = logging.getLogger("AI")

    def _connected(self) -> Any:
        if self._session is None:
            raise ProviderError("Gemini Live session is not connected.")
        return self._session

    async def connect(self) -> None:
        if self._session is not None:
            return
        self._log.info("Connecting to Gemini Live...")
        for attempt in range(3):
            try:
                config = {
                    **_CONFIG,
                    "system_instruction": _CONFIG["system_instruction"]
                    + f"\nCurrent local date: {datetime.now().astimezone().date().isoformat()}.",
                }
                manager = self._client.aio.live.connect(model=self._model, config=config)
                self._session = await manager.__aenter__()
                self._manager = manager
                self._log.info("Connected to Gemini Live")
                return
            except Exception as exc:
                await self._disconnect()
                code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                if code in {400, 401, 403, 429, 1007, 1008} or any(
                    marker in str(exc).lower() for marker in ("api key not valid", "quota", "resource_exhausted")
                ) or attempt == 2:
                    raise ProviderError(self._redact(f"Could not connect to Gemini Live: {exc}")) from exc
                self._log.warning("Gemini connection failed; retrying (%s/3)", attempt + 1)
                await asyncio.sleep(2 ** attempt)

    async def _disconnect(self) -> None:
        manager, self._manager = self._manager, None
        self._session = None
        self._messages = None
        self._pending.clear()
        if manager is not None:
            await manager.__aexit__(None, None, None)

    async def close(self) -> None:
        try:
            await self._disconnect()
        finally:
            await self._client.aio.aclose()

    async def start_turn(self) -> None:
        self._messages = None
        self._pending.clear()
        self._call_names.clear()
        self._activity_started = False
        self._seen_queries.clear()
        self._seen_sources.clear()

    async def send_audio(self, pcm16: bytes) -> None:
        if not self._activity_started:
            await self._connected().send_realtime_input(activity_start=types.ActivityStart())
            self._activity_started = True
        await self._connected().send_realtime_input(
            audio=types.Blob(data=pcm16, mime_type="audio/pcm;rate=16000")
        )

    async def finish_input(self) -> None:
        if self._activity_started:
            await self._connected().send_realtime_input(activity_end=types.ActivityEnd())
            self._activity_started = False

    async def receive(self) -> AIEvent:
        if self._pending:
            return self._pending.popleft()
        if self._messages is None:
            self._messages = self._connected().receive().__aiter__()
        try:
            message = await asyncio.wait_for(anext(self._messages), timeout=20)
        except StopAsyncIteration:
            self._messages = None
            raise ProviderError("Gemini Live stopped before completing the response.")
        except Exception as exc:
            raise ProviderError(self._redact(f"Gemini Live disconnected or timed out: {exc}")) from exc
        self._queue_message(message)
        return self._pending.popleft() if self._pending else AIEvent(EventKind.OTHER)

    def _queue_message(self, message: types.LiveServerMessage) -> None:
        if message.tool_call:
            calls = []
            for fc in message.tool_call.function_calls or []:
                if not fc.id or not fc.name:
                    raise ProviderError("Gemini sent a malformed function call.")
                self._call_names[fc.id] = fc.name
                calls.append(ToolCall(fc.id, fc.name, json.dumps(fc.args or {})))
            if calls:
                self._pending.append(AIEvent(EventKind.DONE, tool_calls=tuple(calls)))
        content = message.server_content
        if content:
            if content.interrupted:
                raise ProviderError("Gemini interrupted the current response.")
            if content.grounding_metadata:
                self._queue_search(content.grounding_metadata)
            if content.model_turn:
                for part in content.model_turn.parts or []:
                    if part.inline_data and part.inline_data.data:
                        self._pending.append(AIEvent(EventKind.AUDIO, audio=part.inline_data.data))
            if content.output_transcription and content.output_transcription.text:
                self._pending.append(AIEvent(EventKind.TRANSCRIPT, transcript=content.output_transcription.text))
            if content.input_transcription and content.input_transcription.text:
                self._pending.append(AIEvent(EventKind.INPUT_TRANSCRIPT, transcript=content.input_transcription.text))
            if content.turn_complete:
                self._pending.append(AIEvent(EventKind.DONE))

    def _queue_search(self, metadata: types.GroundingMetadata) -> None:
        queries = []
        sources = []
        for query in metadata.web_search_queries or []:
            query = " ".join(query.split())
            if query and query not in self._seen_queries:
                self._seen_queries.add(query)
                queries.append(query)
        for chunk in metadata.grounding_chunks or []:
            if not chunk.web or not chunk.web.uri:
                continue
            url = chunk.web.uri.strip()
            try:
                parsed = urlsplit(url)
            except ValueError:
                continue
            if parsed.scheme not in {"http", "https"} or not parsed.netloc or any(c.isspace() for c in url):
                continue
            if url not in self._seen_sources:
                self._seen_sources.add(url)
                title = " ".join((chunk.web.title or parsed.netloc).split())
                sources.append(WebSource(title, url))
        if queries or sources:
            self._pending.append(AIEvent(EventKind.WEB_SEARCH, search_queries=tuple(queries), sources=tuple(sources)))

    async def submit_tool_result(self, call_id: str, output: str) -> None:
        name = self._call_names.pop(call_id, None)
        if name is None:
            raise ProviderError("Unknown Gemini function call ID.")
        await self._connected().send_tool_response(function_responses=[types.FunctionResponse(
            id=call_id, name=name, response=json.loads(output),
        )])

    async def continue_response(self) -> None:
        # Gemini resumes the same turn automatically after send_tool_response.
        return

    def _redact(self, message: str) -> str:
        return message.replace(self._api_key, "[REDACTED]")
