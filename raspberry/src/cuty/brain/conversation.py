"""Push-to-talk conversation orchestration."""

from __future__ import annotations

import asyncio
import json
import logging
import os
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
from cuty.audio.volume import VoiceVolume
from cuty.brain.voice_commands import wants_menu
from cuty.music.commands import MusicCommand, parse_music_command
from cuty.music.protocol import MusicProvider
from cuty.brain.volume_commands import VolumeCommand, parse_volume_command
from cuty.vision.voice_commands import (
    confirmed_enrollment_name, confirmed_forget, is_explicit_cancel,
    may_be_vision_intent, vision_intent,
)

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
        music: MusicProvider | None = None,
        vision=None,
        voice_volume: VoiceVolume | None = None,
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
        self.music = music
        self.vision = vision
        self.voice_volume = voice_volume or VoiceVolume.from_env()
        self._pending_music_command: MusicCommand | None = None
        self._pending_volume_command: VolumeCommand | None = None
        self._music_volume_before_mute: int | None = None
        self._pending_vision_intent: str | None = None
        self._face_consent: str | None = None
        self._last_input_transcript = ""
        self._log = logging.getLogger("CUTY")

    async def greet(self) -> None:
        """Ask the hands-free provider to speak before opening the microphone."""
        self.state.set(State.THINKING)
        try:
            await self.provider.request_greeting()
            # A greeting has no user transcript to release held audio against.
            # Stream it immediately and don't play a thinking aside before "Hola".
            await self._receive_response(greeting=True)
            self.state.set(State.IDLE)
        except Exception:
            self.state.set(State.ERROR)
            raise

    async def run_turn(self, stop: asyncio.Event) -> bool:
        """Record until stop, then stream and play a response. Return False for empty input."""
        if self.state.current == State.ERROR:
            self.state.set(State.IDLE)
        if self.state.current not in {State.IDLE, State.MUSIC_PLAYING, State.MUSIC_PAUSED}:
            raise RuntimeError("A conversation turn is already in progress.")
        music_was_playing = False
        self._pending_music_command = None
        self._pending_volume_command = None
        self._pending_vision_intent = None
        self._last_input_transcript = ""
        try:
            if self.half_duplex:
                if self.music is not None:
                    music_was_playing = (await self.music.get_playback_state()).status == "playing"
                    if music_was_playing:
                        await self.music.pause()
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
                if self.half_duplex:
                    await self.speaker.open()
                if music_was_playing and self.music is not None:
                    await self.music.resume()
                    self.state.set(State.MUSIC_PLAYING)
                elif self.music is not None and (await self.music.get_playback_state()).status == "paused":
                    self.state.set(State.MUSIC_PAUSED)
                return False
            self._log.info("Audio del micrófono enviado: %d bytes PCM16", bytes_sent)
            if self.half_duplex:
                # The microphone generator has closed before playback reopens.
                await self.speaker.open()
            await self.provider.finish_input()
            self.state.set(State.THINKING)
            await self._receive_response()
            self.state.set(State.IDLE)
            if self._pending_vision_intent or self._face_consent:
                await self._handle_vision_request()
            if self.music is not None and self._pending_music_command is not None:
                await self._execute_music_command(self._pending_music_command)
                if self._pending_music_command.action in {"pause", "stop"}:
                    music_was_playing = False
            if music_was_playing and self.music is not None:
                await self.music.resume()
            if self.music is not None:
                playback = await self.music.get_playback_state()
                if playback.status == "playing":
                    self.state.set(State.MUSIC_PLAYING)
                elif playback.status == "paused":
                    self.state.set(State.MUSIC_PAUSED)
            return True
        except ReturnToMenu:
            self.state.set(State.IDLE)
            raise
        except Exception:
            self.state.set(State.ERROR)
            raise

    async def _receive_response(self, *, greeting: bool = False) -> None:
        """Read server events independently of the speaker's blocking playback."""
        audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=64)
        started = monotonic()
        stop_thinking = asyncio.Event()
        abort_thinking = asyncio.Event()
        thinking_task = (
            asyncio.create_task(self.thinking_voice.run(self.speaker, stop_thinking, abort=abort_thinking))
            if self.thinking_voice is not None and not greeting else None
        )

        async def collect() -> None:
            await self._collect_response(audio_queue, greeting=greeting)
            await audio_queue.put(None)

        async def play() -> None:
            first = True
            first_audio_at = None
            write_time = 0.0
            audio_chunks = 0
            while True:
                audio = await audio_queue.get()
                if audio is None:
                    self._log.info(
                        "[AUDIO PERF] response_playback_ms=%.1f speaker_write_ms=%.1f chunks=%d",
                        (monotonic() - (first_audio_at or started)) * 1000,
                        write_time * 1000, audio_chunks,
                    )
                    return
                if first:
                    first_audio_at = monotonic()
                    stop_thinking.set()
                    if thinking_task is not None:
                        await asyncio.shield(thinking_task)
                    self.state.set(State.SPEAKING)
                    self._log.info("Primera voz en %.2f s", monotonic() - started)
                    first = False
                write_started = monotonic()
                await self.speaker.write(audio)
                write_time += monotonic() - write_started
                audio_chunks += 1

        tasks = [asyncio.create_task(collect()), asyncio.create_task(play())]
        try:
            await asyncio.gather(*tasks)
        finally:
            stop_thinking.set()
            abort_thinking.set()
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            if thinking_task is not None:
                await thinking_task

    async def _collect_response(
        self, audio_queue: asyncio.Queue[bytes | None], *, greeting: bool = False,
    ) -> None:
        first_audio = False
        held_audio: list[bytes] = []
        # Normal turns hold initial audio until the transcript distinguishes
        # commands from conversation. The startup greeting has no such input.
        transcript_seen = greeting
        volume_command_applied = False
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
                    if not transcript_seen:
                        held_audio.append(event.audio)
                    elif self._pending_volume_command is not None:
                        held_audio.append(event.audio)
                    elif self._pending_vision_intent is None and self._pending_volume_command is None:
                        await audio_queue.put(event.audio)
                elif event.kind == EventKind.TRANSCRIPT and event.transcript:
                    self._log.info("C.U.T.Y: %s", event.transcript)
                elif event.kind == EventKind.INPUT_TRANSCRIPT and event.transcript:
                    input_transcript += " " + event.transcript
                    self._last_input_transcript = input_transcript.strip()
                    self._pending_volume_command = parse_volume_command(
                        input_transcript, step=self.voice_volume.step
                    )
                    previous_vision_intent = self._pending_vision_intent
                    transcript_seen = True
                    if self._face_consent is None:
                        self._pending_vision_intent = vision_intent(input_transcript)
                    else:
                        self._pending_vision_intent = "consent"
                    if self._pending_vision_intent is not None and previous_vision_intent is None:
                        # Log the action category only; never persist the transcript or image.
                        self._log.info("Intención local detectada: %s", self._pending_vision_intent)
                    if (self._pending_vision_intent is None and self._pending_volume_command is None
                            and not may_be_vision_intent(input_transcript)):
                        self._log.info("Escuché: %s", event.transcript)
                        for audio in held_audio:
                            await audio_queue.put(audio)
                        held_audio.clear()
                    elif self._pending_vision_intent is not None:
                        held_audio.clear()
                    parsed = parse_music_command(input_transcript)
                    if parsed is not None:
                        self._pending_music_command = parsed
                elif event.kind == EventKind.WEB_SEARCH:
                    web_log = logging.getLogger("WEB")
                    for query in event.search_queries:
                        web_log.info("Búsqueda: %s", query)
                    for source in event.sources:
                        web_log.info("Fuente: %s — %s", source.title, source.url)
                elif event.kind == EventKind.DONE:
                    if self._pending_volume_command is not None:
                        command = self._pending_volume_command
                        self._pending_volume_command = None
                        await self._apply_volume_command(command)
                        volume_command_applied = True
                        self._pending_music_command = None
                        if self._pending_vision_intent is None:
                            for audio in held_audio:
                                await audio_queue.put(audio)
                        held_audio.clear()
                    elif self._pending_vision_intent is None and held_audio:
                        for audio in held_audio:
                            await audio_queue.put(audio)
                        held_audio.clear()
                    if self.voice_exit and wants_menu(input_transcript):
                        raise ReturnToMenu
                    if event.tool_calls:
                        for call in event.tool_calls:
                            await self._handle_tool(call, input_transcript=input_transcript)
                        await self.provider.continue_response()
                        break
                    if (not first_audio and self._pending_vision_intent is None
                            and self._face_consent is None and not volume_command_applied):
                        raise ProviderError("La IA terminó el turno sin enviar voz. No se recibió una respuesta hablada.")
                    return
        raise ProviderError("AI provider called tools too many times without finishing a reply.")

    async def _handle_vision_request(self) -> None:
        """Run local vision/consent actions without blocking FaceTracker or audio loops."""
        from cuty.vision.recognition import RecognitionUnavailable

        intent = self._pending_vision_intent
        self._pending_vision_intent = None
        transcript = self._last_input_transcript
        if self._face_consent is not None:
            if is_explicit_cancel(transcript):
                self._face_consent = None
                await self._speak_local("De acuerdo. No guardaré ni borraré ningún rostro.")
                return
            if self._face_consent == "enroll":
                name = confirmed_enrollment_name(transcript)
                if name is None:
                    await self._speak_local("No recibí una confirmación válida. No se guardó nada. Si quieres, vuelve a decir: confirmo guardar mi rostro y llámame, seguido de tu nombre.")
                    self._face_consent = None
                    return
                self._face_consent = None
                if self.vision is None:
                    await self._speak_local("El reconocimiento local no está configurado en este dispositivo; no guardé capturas.")
                    return
                try:
                    result = await asyncio.to_thread(self.vision.enroll, name)
                    await self._speak_local(f"Listo, guardé localmente {result.get('samples', 0)} plantillas para {name}. No guardé las imágenes.")
                except (RecognitionUnavailable, OSError, TimeoutError) as exc:
                    self._log.warning("Registro facial local no disponible (%s)", type(exc).__name__)
                    await self._speak_local("No pude completar el registro local. No guardé imágenes ni datos parciales.")
                except Exception as exc:
                    self._log.exception("Error inesperado durante el registro facial (%s)", type(exc).__name__)
                    await self._speak_local("Ocurrió un error local y no pude completar el registro facial.")
                return
            if self._face_consent == "forget":
                if not confirmed_forget(transcript):
                    await self._speak_local("No recibí la confirmación explícita. No borré ningún dato facial.")
                    self._face_consent = None
                    return
                self._face_consent = None
                if self.vision is None:
                    await self._speak_local("El reconocimiento local no está configurado. No pude borrar perfiles.")
                    return
                try:
                    result = await asyncio.to_thread(self.vision.forget)
                    if result.get("deleted"):
                        message = "He borrado tus plantillas faciales locales. Las de otras personas siguen guardadas."
                    elif result.get("matched"):
                        message = "Ese perfil ya no estaba guardado. No cambié los demás."
                    else:
                        message = "No pude asociar con confianza tu rostro a un perfil. No borré nada."
                    await self._speak_local(message)
                except (RecognitionUnavailable, OSError, TimeoutError) as exc:
                    self._log.warning("Borrado facial local no disponible (%s)", type(exc).__name__)
                    await self._speak_local("No pude borrar el archivo local de perfiles.")
                except Exception as exc:
                    self._log.exception("Error inesperado durante el borrado facial (%s)", type(exc).__name__)
                    await self._speak_local("Ocurrió un error local y no pude borrar las plantillas faciales.")
                return

        if intent in {None, "consent"}:
            return
        if intent == "enroll":
            self._face_consent = "enroll"
            await self._speak_local("Puedo guardar varias plantillas faciales solo en este Raspberry Pi; no guardaré fotos. Para continuar, di: confirmo guardar mi rostro y llámame, seguido de tu nombre. Di cancela para salir.")
            return
        if intent == "forget":
            self._face_consent = "forget"
            await self._speak_local("Esto borrará únicamente las plantillas del rostro que pueda reconocerte con confianza; las demás personas no se borrarán. Para confirmar, di: confirmo, olvida mi rostro. Di cancela para salir.")
            return
        if self.vision is None:
            await self._speak_local("La función de visión local no está conectada. No tomé ni envié ninguna imagen.")
            return
        try:
            if intent == "describe":
                try:
                    capture_started = monotonic()
                    jpeg = await asyncio.to_thread(self.vision.capture_redacted_jpeg)
                    self._log.info("[VISION PERF] capture_ipc_redact_encode_total_ms=%.1f jpeg_bytes=%d",
                                   (monotonic() - capture_started) * 1000, len(jpeg))
                except (RecognitionUnavailable, OSError, TimeoutError, ProviderError) as exc:
                    self._log.warning("Captura local para visión fallida (%s: %s)", type(exc).__name__, self._safe_error(exc))
                    raise
                describe = getattr(self.provider, "describe_image", None)
                if describe is None:
                    raise RecognitionUnavailable("El proveedor activo no admite comprensión de imágenes")
                self._log.info("Captura local lista; solicitando descripción visual")
                try:
                    description = await describe(jpeg, question="¿Qué estás viendo?")
                except (RecognitionUnavailable, OSError, TimeoutError, ProviderError) as exc:
                    self._log.warning("Proveedor de visión falló (%s: %s)", type(exc).__name__, self._safe_error(exc))
                    raise
                self._log.info("Descripción visual recibida; preparando respuesta de voz")
                await self._speak_local(description)
            elif intent == "identify":
                result = await asyncio.to_thread(self.vision.identify)
                if not result.get("known") or not result.get("name"):
                    await self._speak_local("No te reconozco con suficiente confianza.")
                else:
                    await self._speak_local(f"Creo que eres {result['name']}.")
        except (RecognitionUnavailable, OSError, TimeoutError, ProviderError) as exc:
            self._log.warning("Solicitud de visión fallida (%s: %s)", type(exc).__name__, self._safe_error(exc))
            await self._speak_local("No pude completar la solicitud de visión ahora. No envié ni guardé datos faciales.")
        except Exception as exc:
            self._log.exception("Error inesperado de visión (%s)", type(exc).__name__)
            await self._speak_local("Ocurrió un error local al procesar la visión.")

    async def _speak_local(self, text: str) -> None:
        speak = getattr(self.provider, "speak_text", None)
        if speak is None:
            self._log.warning("El proveedor activo no admite respuestas de voz locales")
            return
        self.state.set(State.THINKING)
        started = monotonic()
        try:
            await speak(text)
            await self._receive_response()
            self._log.info("[VISION PERF] local_response_total_ms=%.1f", (monotonic() - started) * 1000)
        except asyncio.CancelledError:
            raise
        except ProviderError as exc:
            # A long multimodal request can outlive Gemini Live's socket. Reconnect
            # and retry only if no answer audio started, so a partial answer is not repeated.
            if self.state.current == State.THINKING and hasattr(self.provider, "close"):
                self._log.warning("Voz local interrumpida; reconectando Gemini Live una vez")
                try:
                    restart = getattr(self.provider, "restart_voice_session", None)
                    if restart is not None:
                        await restart()
                    else:
                        await self.provider.close()
                        await self.provider.connect()
                    await speak(text)
                    await self._receive_response()
                    return
                except asyncio.CancelledError:
                    raise
                except Exception as retry_exc:
                    self._log.warning(
                        "Reintento de voz local falló (%s: %s)",
                        type(retry_exc).__name__, self._safe_error(retry_exc),
                    )
            else:
                self._log.warning("No pude pronunciar una respuesta local (%s: %s)", type(exc).__name__, self._safe_error(exc))
        except Exception as exc:
            self._log.warning("No pude pronunciar una respuesta local (%s: %s)", type(exc).__name__, self._safe_error(exc))
        finally:
            self.state.set(State.IDLE)

    def _safe_error(self, exc: Exception) -> str:
        """Keep useful diagnostics while redacting provider credentials and bounding log size."""
        detail = " ".join(str(exc).split())[:240]
        redact = getattr(self.provider, "_redact", None)
        if callable(redact):
            detail = redact(detail)
        return detail or "sin detalle"

    async def _execute_music_command(self, command: MusicCommand) -> None:
        if self.music is None:
            return
        if command.action == "search" and command.query:
            tracks = await self.music.search_tracks(command.query)
            if tracks:
                await self.music.play(tracks[0].id)
                self._log.info("MUSIC: playing %s — %s", tracks[0].title, tracks[0].artist)
                self.state.set(State.MUSIC_PLAYING)
            else:
                self._log.info("MUSIC: no local matches for %s", command.query)
        elif command.action == "pause":
            await self.music.pause()
            if (await self.music.get_playback_state()).status == "paused":
                self.state.set(State.MUSIC_PAUSED)
        elif command.action == "resume":
            await self.music.resume()
            if (await self.music.get_playback_state()).status == "playing":
                self.state.set(State.MUSIC_PLAYING)
        elif command.action == "stop":
            await self.music.stop()
            self.state.set(State.IDLE)
        elif command.action == "next":
            await self.music.next()
            if (await self.music.get_playback_state()).status == "playing":
                self.state.set(State.MUSIC_PLAYING)
        elif command.action == "previous":
            await self.music.previous()
            if (await self.music.get_playback_state()).status == "playing":
                self.state.set(State.MUSIC_PLAYING)
        elif command.action == "set_volume" and command.volume is not None:
            await self.music.set_volume(command.volume)
        elif command.action == "volume_up":
            current = await self.music.get_playback_state()
            await self.music.set_volume(min(100, current.volume + 10))
        elif command.action == "volume_down":
            current = await self.music.get_playback_state()
            await self.music.set_volume(max(0, current.volume - 10))
        elif command.action == "get_current_track":
            current = await self.music.get_playback_state()
            self._log.info("MUSIC: current track %s", current.track.title if current.track else "none")

    async def _apply_volume_command(self, command: VolumeCommand) -> None:
        """Apply validated voice volume instructions before releasing reply audio."""
        target = command.target
        if target == "active":
            try:
                playback = await self.music.get_playback_state() if self.music is not None else None
            except Exception as exc:
                self._log.warning("No pude leer estado de música para volumen (%s)", type(exc).__name__)
                playback = None
            target = "music" if playback is not None and playback.status in {"playing", "paused"} else "voice"

        targets = {"both"} if target == "both" else {target}
        for selected in targets:
            if selected == "voice":
                if command.action == "mute":
                    value = self.voice_volume.mute()
                elif command.action == "unmute":
                    value = self.voice_volume.unmute()
                elif command.action == "set":
                    value = self.voice_volume.set(command.value)
                else:
                    value = self.voice_volume.adjust(command.value or 0)
                self._log.info("[VOLUME] voice=%d%%", value)
            elif selected == "music":
                if self.music is None:
                    self._log.warning("[VOLUME] No hay proveedor de música activo")
                    continue
                try:
                    playback = await self.music.get_playback_state()
                    if command.action == "mute":
                        if playback.volume > 0:
                            self._music_volume_before_mute = playback.volume
                        value = 0
                    elif command.action == "unmute":
                        value = self._music_volume_before_mute or max(1, int(os.getenv("CUTY_MUSIC_VOLUME", "70")))
                        self._music_volume_before_mute = None
                    elif command.action == "set":
                        value = command.value
                        if value == 0 and playback.volume > 0:
                            self._music_volume_before_mute = playback.volume
                        elif value > 0:
                            self._music_volume_before_mute = None
                    else:
                        value = max(0, min(100, playback.volume + (command.value or 0)))
                        if value == 0 and playback.volume > 0:
                            self._music_volume_before_mute = playback.volume
                        elif value > 0:
                            self._music_volume_before_mute = None
                    await self.music.set_volume(value)
                    self._log.info("[VOLUME] music=%d%%", value)
                except Exception as exc:
                    self._log.warning("[VOLUME] No pude cambiar volumen de música (%s)", type(exc).__name__)

    async def _handle_tool(self, call: ToolCall, *, input_transcript: str = "") -> None:
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
                if not wants_menu(input_transcript):
                    raise ValueError("No explicit exit command was transcribed")
                await self.provider.submit_tool_result(call.call_id, json.dumps({"ok": True}))
                raise ReturnToMenu
            else:
                raise ValueError("Unknown tool")
        except WebSearchError as exc:
            logging.getLogger("WEB").warning("%s", exc)
            result = {"ok": False, "error": str(exc), "results": []}
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            self._log.warning("Rejected tool %s: %s", call.name, exc)
            error = ("Invalid search arguments" if call.name == "search_web" else
                     "Exit not confirmed by the user's transcription; continue the conversation"
                     if call.name == "return_to_menu" else "Invalid expression arguments")
            result = {"ok": False, "error": error}
        await self.provider.submit_tool_result(call.call_id, json.dumps(result))
