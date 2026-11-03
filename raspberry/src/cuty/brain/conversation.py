"""Push-to-talk conversation orchestration."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import asdict
from contextlib import aclosing
from time import monotonic

from cuty.llm.provider import AIProvider, EventKind, ProviderError, ToolCall
from cuty.audio.microphone import Microphone
from cuty.audio.speaker import Speaker
from cuty.brain.states import State, StateMachine
from cuty.face.expressions import Expression
from cuty.face.expression_sink import ExpressionController
from cuty.llm.web_search import WebSearchError, WebSearchService
from cuty.audio.thinking import ThinkingVoice
from cuty.brain.voice_commands import wants_menu

RESPONSE_START_TIMEOUT = 15.0


class ReturnToMenu(Exception):
    """Normal termination requested by the user, not a provider failure."""


class ConversationService:
    def __init__(
        self,
        provider: AIProvider,
        microphone: Microphone,
        speaker: Speaker,
        state: StateMachine,
        expressions: ExpressionController,
        web_search: WebSearchService | None = None,
        thinking_voice: ThinkingVoice | None = None,
        voice_exit: bool = False,
        half_duplex: bool = False,
    ) -> None:
        self.provider = provider
        self.microphone = microphone
        self.speaker = speaker
        self.state = state
        self.expressions = expressions
        self.web_search = web_search or WebSearchService()
        self.thinking_voice = thinking_voice
        self.voice_exit = voice_exit
        self.half_duplex = half_duplex
        self._log = logging.getLogger("CUTY")

    async def greet(self) -> None:
        """Ask the hands-free provider to speak before opening the microphone."""
        self.state.set(State.THINKING)
        try:
            await self.provider.request_greeting()
            await self._receive_response()
            self.state.set(State.IDLE)
        except Exception:
            self.state.set(State.ERROR)
            raise

    async def run_turn(self, stop: asyncio.Event) -> bool:
        """Record until stop, then stream and play a response. Return False for empty input."""
        if self.state.current != State.IDLE:
            raise RuntimeError("A conversation turn is already in progress.")
        try:
            if self.half_duplex:
                # Release the physical playback stream, not just its audio queue.
                # Some I2S HATs cannot reliably start capture while it is open.
                await self.speaker.close()
                await asyncio.sleep(0.1)
            await self.provider.start_turn()
            self.state.set(State.LISTENING)
            chunks = 0
            bytes_sent = 0
            async with aclosing(self.microphone.chunks(stop)) as source:
                async for pcm16 in source:
                    if pcm16:
                        await self.provider.send_audio(pcm16)
                        chunks += 1
                        bytes_sent += len(pcm16)
            if chunks == 0:
                self._log.warning("No se capturó audio del micrófono.")
                self.state.set(State.IDLE)
                return False
            self._log.info("Audio del micrófono enviado: %d bytes PCM16", bytes_sent)
            if self.half_duplex:
                # The microphone generator has closed before playback reopens.
                await self.speaker.open()
            await self.provider.finish_input()
            self.state.set(State.THINKING)
            await self._receive_response()
            self.state.set(State.IDLE)
            return True
        except ReturnToMenu:
            self.state.set(State.IDLE)
            raise
        except Exception:
            self.state.set(State.ERROR)
            raise

    async def _receive_response(self) -> None:
        """Read server events independently of the speaker's blocking playback."""
        audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=64)
        started = monotonic()
        stop_thinking = asyncio.Event()
        thinking_task = (
            asyncio.create_task(self.thinking_voice.run(self.speaker, stop_thinking))
            if self.thinking_voice is not None else None
        )

        async def collect() -> None:
            await self._collect_response(audio_queue)
            await audio_queue.put(None)

        async def play() -> None:
            first = True
            while True:
                audio = await audio_queue.get()
                if audio is None:
                    return
                if first:
                    stop_thinking.set()
                    if thinking_task is not None:
                        await asyncio.shield(thinking_task)
                    self.state.set(State.SPEAKING)
                    self._log.info("Primera voz en %.2f s", monotonic() - started)
                    first = False
                await self.speaker.write(audio)

        tasks = [asyncio.create_task(collect()), asyncio.create_task(play())]
        try:
            await asyncio.gather(*tasks)
        finally:
            stop_thinking.set()
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            if thinking_task is not None:
                await thinking_task

    async def _collect_response(self, audio_queue: asyncio.Queue[bytes | None]) -> None:
        first_audio = False
        input_transcript = ""
        deadline = monotonic() + RESPONSE_START_TIMEOUT
        # A function call can require another response before speech begins.
        for _ in range(5):
            while True:
                try:
                    if first_audio:
                        event = await self.provider.receive()
                    else:
                        remaining = deadline - monotonic()
                        if remaining <= 0:
                            raise TimeoutError
                        event = await asyncio.wait_for(self.provider.receive(), timeout=remaining)
                except TimeoutError as exc:
                    raise ProviderError(
                        "La IA no empezó a hablar en 15 segundos. Revisa la conexión y la cuota de Gemini."
                    ) from exc
                if event.kind == EventKind.AUDIO:
                    if not event.audio or len(event.audio) % 2:
                        raise ProviderError("AI provider sent invalid PCM16 audio.")
                    first_audio = True
                    await audio_queue.put(event.audio)
                elif event.kind == EventKind.TRANSCRIPT and event.transcript:
                    self._log.info("C.U.T.Y: %s", event.transcript)
                elif event.kind == EventKind.INPUT_TRANSCRIPT and event.transcript:
                    self._log.info("Escuché: %s", event.transcript)
                    input_transcript += " " + event.transcript
                elif event.kind == EventKind.WEB_SEARCH:
                    web_log = logging.getLogger("WEB")
                    for query in event.search_queries:
                        web_log.info("Búsqueda: %s", query)
                    for source in event.sources:
                        web_log.info("Fuente: %s — %s", source.title, source.url)
                elif event.kind == EventKind.DONE:
                    if self.voice_exit and wants_menu(input_transcript):
                        raise ReturnToMenu
                    if event.tool_calls:
                        for call in event.tool_calls:
                            await self._handle_tool(call)
                        await self.provider.continue_response()
                        break
                    if not first_audio:
                        raise ProviderError("La IA terminó el turno sin enviar voz. No se recibió una respuesta hablada.")
                    return
        raise ProviderError("AI provider called tools too many times without finishing a reply.")

    async def _handle_tool(self, call: ToolCall) -> None:
        result: dict[str, object]
        try:
            args = json.loads(call.arguments)
            if not isinstance(args, dict):
                raise ValueError("Malformed tool arguments")
            if call.name == "search_web":
                if set(args) != {"query"} or not isinstance(args["query"], str):
                    raise ValueError("Malformed search query")
                query = " ".join(args["query"].split())
                if not query or len(query) > 400:
                    raise ValueError("Search query must have 1 to 400 characters")
                web_log = logging.getLogger("WEB")
                web_log.info("Buscando: %s", query)
                sources = await self.web_search.search(query)
                for source in sources:
                    web_log.info("Fuente: %s — %s", source.title, source.url)
                result = {"ok": True, "query": query, "results": [asdict(source) for source in sources]}
            elif call.name == "set_expression":
                if set(args) != {"expression", "intensity"}:
                    raise ValueError("Malformed expression arguments")
                expression = Expression(args["expression"])
                event = self.expressions.set_emotion(expression, args["intensity"])
                result = {"ok": True, "event": event.as_dict()}
            elif call.name == "return_to_menu" and self.voice_exit:
                if args:
                    raise ValueError("Return to menu takes no arguments")
                await self.provider.submit_tool_result(call.call_id, json.dumps({"ok": True}))
                raise ReturnToMenu
            else:
                raise ValueError("Unknown tool")
        except WebSearchError as exc:
            logging.getLogger("WEB").warning("%s", exc)
            result = {"ok": False, "error": str(exc), "results": []}
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            self._log.warning("Rejected model expression event: %s", exc)
            result = {"ok": False, "error": "Invalid search arguments" if call.name == "search_web" else "Invalid expression arguments"}
        await self.provider.submit_tool_result(call.call_id, json.dumps(result))
