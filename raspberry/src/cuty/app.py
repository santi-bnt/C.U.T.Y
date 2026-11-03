"""Windows command line entry point; audio backend is portable to Raspberry Pi OS."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import queue
import signal
import threading
from pathlib import Path

from dotenv import load_dotenv

from cuty.llm.openai_provider import OpenAIRealtimeProvider
from cuty.llm.gemini_provider import GeminiLiveProvider
from cuty.audio.devices import AudioDeviceError, format_devices, list_devices, select_working_device, test_microphone_level
from cuty.audio.activity import SpeechMicrophone
from cuty.audio.microphone import SoundDeviceMicrophone
from cuty.audio.speaker import SoundDeviceSpeaker
from cuty.audio.remote import RemoteSpeaker, serve_audio
from cuty.brain.conversation import ConversationService, ReturnToMenu
from cuty.brain.states import State, StateMachine
from cuty.config import Config, ConfigurationError
from cuty.audio.thinking import ThinkingVoice
from cuty.audio.lipsync import LipSyncSpeaker
from cuty.face.expression_sink import (
    CompositeExpressionSink, ConsoleExpressionSink, ExpressionController, FaceLinkExpressionSink,
)
from cuty.face.link import FaceLinkSender
from cuty.utils.logging import configure_logging


class Keyboard:
    """One daemon reader avoids leaving blocked executor threads after Ctrl+C."""

    def __init__(self) -> None:
        self._lines: queue.Queue[str | None] = queue.Queue()
        threading.Thread(target=self._read, daemon=True, name="cuty-keyboard").start()

    def _read(self) -> None:
        try:
            while True:
                self._lines.put(input())
        except EOFError:
            self._lines.put(None)

    async def line(self, prompt: str) -> str | None:
        print(prompt, flush=True)
        while True:
            try:
                return self._lines.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.05)


async def run_hands_free(service: ConversationService) -> None:
    await service.greet()
    service.voice_exit = True
    try:
        while True:
            # Let the final speaker buffers / room echo settle before reopening the mic.
            await asyncio.sleep(0.25)
            await service.run_turn(asyncio.Event())
    except ReturnToMenu:
        logging.getLogger("CUTY").info("Volviendo al menú principal por petición de voz.")


async def run(config: Config, *, hands_free: bool = False) -> int:
    log = logging.getLogger("CUTY")
    log.info("Starting...")
    if hands_free and config.provider != "gemini":
        raise ConfigurationError("El modo de conversación del menú requiere CUTY_AI_PROVIDER=gemini.")
    if hands_free:
        # Stop the child cleanly when the touchscreen user leaves by holding it.
        try:
            asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, asyncio.current_task().cancel)
        except (NotImplementedError, RuntimeError):
            pass
    input_rate = 16_000 if config.provider == "gemini" else 24_000
    input_selector, output_selector = config.input_device, config.output_device
    if hands_free and (not input_selector or not output_selector):
        # PortAudio indices change across boots: prefer the HAT by identity.
        for device in list_devices():
            if "seeed2micvoicec" in str(device["name"]).lower():
                if not input_selector and device["inputs"]:
                    input_selector = str(device["index"])
                if not output_selector and device["outputs"]:
                    output_selector = str(device["index"])
    input_id, input_name = select_working_device(input_selector, input_device=True, sample_rate=input_rate)
    remote_output = os.getenv("CUTY_AUDIO_REMOTE_OUTPUT")
    if remote_output:
        speaker = RemoteSpeaker(remote_output)
        output_name = f"PC via {remote_output}"
    else:
        output_id, output_name = select_working_device(output_selector, input_device=False)
        speaker = SoundDeviceSpeaker(output_id)
    logging.getLogger("AUDIO").info("Microphone: %s", input_name)
    logging.getLogger("AUDIO").info("Speaker: %s", output_name)

    # The animated face (touchscreen launcher) listens on a local UDP port.
    face_link = FaceLinkSender.from_env()
    sink = ConsoleExpressionSink()
    if face_link is not None:
        sink = CompositeExpressionSink(sink, FaceLinkExpressionSink(face_link))
        log.info("Cara animada: enviando expresiones y boca a %s:%d", *face_link.address)
    expressions = ExpressionController(sink)
    state = StateMachine(expressions.on_state)
    expressions.on_state(State.IDLE)
    provider = (
        GeminiLiveProvider(config.api_key, config.model, hands_free=hands_free)
        if config.provider == "gemini"
        else OpenAIRealtimeProvider(config.api_key, config.model)
    )
    if face_link is not None:
        speaker = LipSyncSpeaker(speaker, face_link)
    thinking_voice = ThinkingVoice()
    prepare_thinking = asyncio.create_task(thinking_voice.prepare())
    try:
        await speaker.open()
        await provider.connect()
        microphone = SoundDeviceMicrophone(input_id, input_rate)
        if hands_free:
            microphone = SpeechMicrophone.from_env(microphone, input_rate)
        service = ConversationService(
            provider, microphone, speaker, state, expressions,
            thinking_voice=thinking_voice,
            half_duplex=hands_free,
        )
        if hands_free:
            await run_hands_free(service)
            return 0
        keyboard = Keyboard()
        while True:
            answer = await keyboard.line("Pulsa ENTER para hablar, o escribe q y ENTER para salir.")
            if answer is None or answer.strip().lower() in {"q", "quit", "exit"}:
                break
            stop = asyncio.Event()

            async def stop_on_enter() -> None:
                await keyboard.line("Habla ahora. Pulsa ENTER al terminar para que C.U.T.Y responda.")
                stop.set()

            stop_task = asyncio.create_task(stop_on_enter())
            try:
                await service.run_turn(stop)
            finally:
                stop_task.cancel()
                await asyncio.gather(stop_task, return_exceptions=True)
        return 0
    finally:
        prepare_thinking.cancel()
        await asyncio.gather(prepare_thinking, return_exceptions=True)
        try:
            await provider.close()
        finally:
            await speaker.close()
            if face_link is not None:
                face_link.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="C.U.T.Y voice companion")
    parser.add_argument("--list-audio-devices", action="store_true", help="List microphone and speaker device indices")
    parser.add_argument("--test-microphone", action="store_true", help="Measure microphone level for 3 seconds without an API key")
    parser.add_argument("--serve-audio", action="store_true", help="Play Pi audio on this PC through an SSH reverse tunnel; no API key needed")
    parser.add_argument("--hands-free", action="store_true", help="Greet, listen without ENTER, and exit by voice (Gemini)")
    args = parser.parse_args()
    configure_logging()
    env_file = Path(__file__).resolve().parents[2] / ".env"
    # Keep the repository-root .env supported by older desktop checkouts.
    load_dotenv(env_file if env_file.is_file() else env_file.parent.parent / ".env")
    try:
        if args.list_audio_devices:
            print(format_devices())
            return 0
        if args.serve_audio:
            output_id, output_name = select_working_device(os.getenv("CUTY_AUDIO_OUTPUT_DEVICE"), input_device=False)
            print(f"PC speaker: {output_name}", flush=True)
            asyncio.run(serve_audio(output_id))
            return 0
        if args.test_microphone:
            print("Speak into your microphone for 3 seconds...", flush=True)
            name, peak, rms = test_microphone_level(os.getenv("CUTY_AUDIO_INPUT_DEVICE"))
            print(f"Microphone: {name}\nPeak: {peak:.1f}%  RMS: {rms:.1f}%")
            if peak < 1.0:
                print("Very low input. Check Windows microphone permission, mute, and input device.")
            return 0
        config = Config.from_env()
        configure_logging("DEBUG" if config.debug else config.log_level)
        return asyncio.run(run(config, hands_free=args.hands_free))
    except asyncio.CancelledError:
        return 0
    except Exception as exc:
        logging.getLogger("CUTY").error("%s", exc)
        return 1
    except KeyboardInterrupt:
        logging.getLogger("CUTY").info("Stopped")
        return 130
