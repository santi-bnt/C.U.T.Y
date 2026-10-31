"""Windows command line entry point; audio backend is portable to Raspberry Pi OS."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import queue
import threading

from dotenv import load_dotenv

from cuty.llm.openai_provider import OpenAIRealtimeProvider
from cuty.llm.gemini_provider import GeminiLiveProvider
from cuty.audio.devices import AudioDeviceError, format_devices, select_working_device, test_microphone_level
from cuty.audio.microphone import SoundDeviceMicrophone
from cuty.audio.speaker import SoundDeviceSpeaker
from cuty.brain.conversation import ConversationService
from cuty.brain.states import State, StateMachine
from cuty.config import Config, ConfigurationError
from cuty.audio.thinking import ThinkingVoice
from cuty.face.expression_sink import ConsoleExpressionSink, ExpressionController
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


async def run(config: Config) -> int:
    log = logging.getLogger("CUTY")
    log.info("Starting...")
    input_rate = 16_000 if config.provider == "gemini" else 24_000
    input_id, input_name = select_working_device(config.input_device, input_device=True, sample_rate=input_rate)
    output_id, output_name = select_working_device(config.output_device, input_device=False)
    logging.getLogger("AUDIO").info("Microphone: %s", input_name)
    logging.getLogger("AUDIO").info("Speaker: %s", output_name)

    expressions = ExpressionController(ConsoleExpressionSink())
    state = StateMachine(expressions.on_state)
    expressions.on_state(State.IDLE)
    provider = (
        GeminiLiveProvider(config.api_key, config.model)
        if config.provider == "gemini"
        else OpenAIRealtimeProvider(config.api_key, config.model)
    )
    speaker = SoundDeviceSpeaker(output_id)
    thinking_voice = ThinkingVoice()
    prepare_thinking = asyncio.create_task(thinking_voice.prepare())
    try:
        await speaker.open()
        await provider.connect()
        service = ConversationService(
            provider, SoundDeviceMicrophone(input_id, input_rate), speaker, state, expressions,
            thinking_voice=thinking_voice,
        )
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


def main() -> int:
    parser = argparse.ArgumentParser(description="C.U.T.Y voice companion")
    parser.add_argument("--list-audio-devices", action="store_true", help="List microphone and speaker device indices")
    parser.add_argument("--test-microphone", action="store_true", help="Measure microphone level for 3 seconds without an API key")
    args = parser.parse_args()
    configure_logging()
    load_dotenv()
    try:
        if args.list_audio_devices:
            print(format_devices())
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
        return asyncio.run(run(config))
    except Exception as exc:
        logging.getLogger("CUTY").error("%s", exc)
        return 1
    except KeyboardInterrupt:
        logging.getLogger("CUTY").info("Stopped")
        return 130
