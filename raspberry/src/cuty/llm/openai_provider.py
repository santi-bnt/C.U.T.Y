"""Official OpenAI Python SDK Realtime WebSocket adapter."""

from __future__ import annotations

import asyncio
import base64
import binascii
import logging
from typing import Any

from openai import AsyncOpenAI
from openai.resources.realtime.realtime import AsyncRealtimeConnection

from cuty.llm.provider import AIEvent, EventKind, ProviderError, ToolCall
from cuty.brain.personality import INSTRUCTIONS
from cuty.face.expressions import Expression


_EMOTIONS = [e.value for e in Expression if e.value not in {"idle", "listening", "thinking", "speaking"}]
_TOOL = {
    "type": "function",
    "name": "set_expression",
    "description": "Show a temporary emotion on C.U.T.Y's future face while responding.",
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {"type": "string", "enum": _EMOTIONS},
            "intensity": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": ["expression", "intensity"],
        "additionalProperties": False,
    },
}


class OpenAIRealtimeProvider:
    def __init__(self, api_key: str, model: str = "gpt-realtime-2.1") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._api_key = api_key
        self._model = model
        self._connection: AsyncRealtimeConnection | None = None
        self._log = logging.getLogger("AI")

    def _conn(self) -> AsyncRealtimeConnection:
        if self._connection is None:
            raise ProviderError("Realtime session is not connected.")
        return self._connection

    async def connect(self) -> None:
        if self._connection is not None:
            return
        self._log.info("Connecting...")
        for attempt in range(3):
            try:
                connection = await self._client.realtime.connect(model=self._model, max_retries=0).enter()
                self._connection = connection
                await connection.session.update(session={
                    "type": "realtime",
                    "model": self._model,
                    "instructions": INSTRUCTIONS,
                    "output_modalities": ["audio"],
                    "audio": {
                        "input": {"format": {"type": "audio/pcm", "rate": 24000}, "turn_detection": None},
                        "output": {"format": {"type": "audio/pcm", "rate": 24000}, "voice": "marin"},
                    },
                    "tools": [_TOOL],
                    "tool_choice": "auto",
                })
                while True:
                    event = await asyncio.wait_for(connection.recv(), timeout=15)
                    if event.type == "session.updated":
                        self._log.info("Connected")
                        return
                    if event.type == "error":
                        raise ProviderError(self._safe_error(event))
            except Exception as exc:
                await self._disconnect()
                if isinstance(exc, ProviderError) or getattr(exc, "status_code", None) in {401, 403}:
                    raise ProviderError(self._redact(f"OpenAI rejected the session: {exc}")) from exc
                if attempt == 2:
                    raise ProviderError(self._redact(f"Could not connect to OpenAI Realtime after 3 attempts: {exc}")) from exc
                self._log.warning("Connection failed; retrying (%s/3)", attempt + 1)
                await asyncio.sleep(2 ** attempt)

    async def _disconnect(self) -> None:
        if self._connection is not None:
            connection, self._connection = self._connection, None
            await connection.close()

    async def close(self) -> None:
        await self._disconnect()
        await self._client.close()

    async def start_turn(self) -> None:
        await self._conn().input_audio_buffer.clear()

    async def send_audio(self, pcm16: bytes) -> None:
        await self._conn().input_audio_buffer.append(audio=base64.b64encode(pcm16).decode("ascii"))

    async def finish_input(self) -> None:
        connection = self._conn()
        await connection.input_audio_buffer.commit()
        await connection.response.create()

    async def receive(self) -> AIEvent:
        try:
            event = await asyncio.wait_for(self._conn().recv(), timeout=45)
        except Exception as exc:
            raise ProviderError(self._redact(f"Realtime session timed out or disconnected: {exc}")) from exc
        if event.type == "error":
            raise ProviderError(self._safe_error(event))
        if event.type == "response.output_audio.delta":
            try:
                return AIEvent(EventKind.AUDIO, audio=base64.b64decode(event.delta, validate=True))
            except (binascii.Error, ValueError) as exc:
                raise ProviderError("OpenAI sent malformed audio data.") from exc
        if event.type == "response.output_audio_transcript.done":
            return AIEvent(EventKind.TRANSCRIPT, transcript=event.transcript)
        if event.type == "response.done":
            if event.response.status != "completed":
                raise ProviderError(f"OpenAI response ended with status {event.response.status}.")
            calls = tuple(
                ToolCall(item.call_id, item.name, item.arguments)
                for item in event.response.output
                if item.type == "function_call"
            )
            return AIEvent(EventKind.DONE, tool_calls=calls)
        self._log.debug("Realtime event: %s", event.type)
        return AIEvent(EventKind.OTHER)

    async def submit_tool_result(self, call_id: str, output: str) -> None:
        await self._conn().conversation.item.create(item={
            "type": "function_call_output", "call_id": call_id, "output": output,
        })

    async def continue_response(self) -> None:
        await self._conn().response.create()

    def _safe_error(self, event: Any) -> str:
        error = getattr(event, "error", None)
        code = getattr(error, "code", None) or "realtime_error"
        message = getattr(error, "message", None) or "Unknown Realtime error"
        return self._redact(f"OpenAI Realtime error ({code}): {message}")

    def _redact(self, message: str) -> str:
        return message.replace(self._api_key, "[REDACTED]")
