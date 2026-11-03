"""Hands-free audio boundaries and spoken menu commands, without hardware."""

import asyncio
from array import array

import pytest

from cuty.audio.activity import SpeechMicrophone
from cuty.app import run_hands_free
from cuty.brain.conversation import ReturnToMenu
from cuty.brain.voice_commands import wants_menu


@pytest.mark.parametrize("text", [
    "Salir.", "¡Quiero salir!", "Cuty, quiero salir, por favor.",
    "Regresa al menú principal", "Quiero salir de Cuty", "salir Cuty",
])
def test_direct_exit_commands(text):
    assert wants_menu(text)


@pytest.mark.parametrize("text", [
    "No quiero salir", "Quiero salir a caminar", "¿Qué significa salir?",
    "Explícame cómo volver al menú", "Mi amigo dice quiero salir", "Hola",
])
def test_conversation_about_exiting_does_not_exit(text):
    assert not wants_menu(text)


class Microphone:
    def __init__(self, levels):
        self.levels = levels
        self.closed = False
        self.read = 0

    async def chunks(self, stop):
        try:
            for level in self.levels:
                if stop.is_set():
                    break
                self.read += 1
                yield array("h", [level] * 320).tobytes()  # 20 ms at 16 kHz
        finally:
            self.closed = True


def capture(levels, **kwargs):
    mic = Microphone(levels)
    stop = asyncio.Event()

    async def run():
        return [pcm async for pcm in SpeechMicrophone(mic, 16000, **kwargs).chunks(stop)]

    return asyncio.run(run()), mic, stop


def test_silence_and_a_short_click_never_start_a_turn():
    chunks, mic, stop = capture([0] * 30 + [2000] * 2 + [0] * 60)
    assert chunks == []
    assert mic.closed
    assert not stop.is_set()


def test_speech_has_preroll_and_ends_after_silence_not_a_short_pause():
    chunks, mic, stop = capture([0] * 30 + [1200] * 15 + [0] * 10 + [1200] * 15 + [0] * 100)
    assert mic.read == 30 + 15 + 10 + 15 + 45
    assert stop.is_set() and mic.closed
    samples = [array("h", chunk)[0] for chunk in chunks]
    assert samples[0] == 0  # Retains the onset instead of clipping the first word.
    assert samples.count(1200) == 30


def test_continuous_noise_cannot_record_forever():
    chunks, mic, stop = capture([2000] * 100, maximum=0.5)
    assert chunks and stop.is_set() and mic.closed
    assert mic.read < 40


def test_speech_can_start_with_short_quiet_consonants_between_voiced_frames():
    # Six voiced frames in 240 ms, with small gaps: no 120 ms continuous vowel.
    chunks, mic, stop = capture([0] * 30 + [1200, 0] * 8 + [0] * 100)
    assert chunks and stop.is_set() and mic.closed
    assert sum(array("h", chunk)[0] == 1200 for chunk in chunks) == 8


def test_idle_level_diagnostics_distinguish_low_level_from_missing_pcm(caplog):
    with caplog.at_level("INFO", logger="AUDIO"):
        chunks, mic, _ = capture([100] * 260)
    assert not chunks and mic.closed
    assert "Micrófono entregando audio" in caplog.text
    assert "Esperando voz" in caplog.text


def test_cancelling_listener_closes_microphone():
    async def run():
        closed = asyncio.Event()

        class WaitingMic:
            async def chunks(self, stop):
                try:
                    yield array("h", [0] * 320).tobytes()
                    await asyncio.Event().wait()
                finally:
                    closed.set()

        source = SpeechMicrophone(WaitingMic(), 16000).chunks(asyncio.Event())
        task = asyncio.create_task(anext(source))
        await asyncio.sleep(0)
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        assert closed.is_set()

    asyncio.run(run())


def test_greeting_then_conversation_then_normal_exit_without_keyboard():
    class Service:
        voice_exit = False
        greeted = False
        turns = 0

        async def greet(self):
            assert not self.voice_exit
            self.greeted = True

        async def run_turn(self, stop):
            assert self.greeted and self.voice_exit
            self.turns += 1
            if self.turns == 2:
                raise ReturnToMenu

    service = Service()
    asyncio.run(run_hands_free(service))
    assert service.turns == 2


def test_app_greets_then_exits_by_voice_and_closes_devices(monkeypatch):
    from types import SimpleNamespace

    from cuty import app
    from cuty.config import Config
    from cuty.llm.provider import AIEvent, EventKind
    from test_conversation import FakeProvider, FakeSpeaker

    lifecycle = []
    provider = FakeProvider([
        AIEvent(EventKind.AUDIO, audio=b"\x00\x00" * 480), AIEvent(EventKind.DONE),
        AIEvent(EventKind.INPUT_TRANSCRIPT, transcript="Quiero salir."), AIEvent(EventKind.DONE),
    ])
    speaker = FakeSpeaker()
    speaker.active = False

    async def greeting():
        lifecycle.append("greeting")

    async def close_provider():
        lifecycle.append("provider closed")

    async def close_speaker():
        if speaker.active:
            lifecycle.append("speaker closed")
        speaker.active = False

    async def open_speaker():
        assert not speaker.active
        speaker.active = True
        lifecycle.append("speaker opened")

    class Mic:
        def __init__(self, device, rate):
            assert device == 7 and rate == 16000

        async def chunks(self, stop):
            assert speaker.audio  # Greeting was actually played before listening.
            assert not speaker.active  # Physical output must be closed during capture.
            lifecycle.append("listening")
            try:
                yield b"\x00\x00" * 320
                stop.set()
            finally:
                lifecycle.append("microphone closed")

    class Thinking:
        async def prepare(self):
            pass

        async def run(self, speaker, stop):
            await stop.wait()

    def select(selector, *, input_device, sample_rate=24000):
        assert selector == "7"
        return 7, "seeed2micvoicec"

    def no_keyboard():
        pytest.fail("Hands-free mode must not read stdin")

    provider.request_greeting = greeting
    provider.close = close_provider
    speaker.close = close_speaker
    speaker.open = open_speaker
    monkeypatch.setattr(app, "list_devices", lambda: [
        {"index": 7, "name": "seeed2micvoicec", "inputs": 2, "outputs": 2},
    ])
    monkeypatch.setattr(app, "select_working_device", select)
    monkeypatch.setattr(app, "GeminiLiveProvider", lambda *a, **kw: provider)
    monkeypatch.setattr(app, "SoundDeviceSpeaker", lambda device: speaker)
    monkeypatch.setattr(app, "SoundDeviceMicrophone", Mic)
    monkeypatch.setattr(app, "SpeechMicrophone", SimpleNamespace(from_env=lambda mic, rate: mic))
    monkeypatch.setattr(app, "ThinkingVoice", Thinking)
    monkeypatch.setattr(app, "Keyboard", no_keyboard)
    monkeypatch.setattr(app.FaceLinkSender, "from_env", lambda: None)
    monkeypatch.delenv("CUTY_AUDIO_REMOTE_OUTPUT", raising=False)
    assert asyncio.run(app.run(Config(api_key="fake-key"), hands_free=True)) == 0
    assert lifecycle == ["speaker opened", "greeting", "speaker closed", "listening",
                         "microphone closed", "speaker opened", "provider closed", "speaker closed"]
