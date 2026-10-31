import asyncio

import pytest

from cuty.audio.thinking import CHUNK_BYTES, PHRASES, ThinkingVoice
from cuty.llm.provider import AIEvent, EventKind, ProviderError
from cuty.brain.states import State
from test_conversation import make_service


def test_selection_does_not_repeat_consecutive_phrases():
    voice = ThinkingVoice()
    voice.clips = {phrase: b"\x01\x00" for phrase in PHRASES}
    previous = None
    for _ in range(50):
        phrase, pcm = voice.choose()
        assert phrase != previous
        assert pcm == b"\x01\x00"
        previous = phrase


def test_fast_response_has_no_thinking_audio():
    answer = b"\x02\x00" * 480
    service, _, speaker, _, _ = make_service([
        AIEvent(EventKind.AUDIO, audio=answer), AIEvent(EventKind.DONE),
    ])
    service.thinking_voice = ThinkingVoice(delay=0.1)
    service.thinking_voice.clips = {PHRASES[0]: b"\x01\x00" * 480}
    asyncio.run(service.run_turn(asyncio.Event()))
    assert speaker.audio == [answer]


def test_answer_stops_filler_without_overlapping_writes():
    async def exercise():
        answer = b"\x02\x00" * 480
        service, provider, speaker, _, state = make_service([
            AIEvent(EventKind.AUDIO, audio=answer), AIEvent(EventKind.DONE),
        ])
        filler_started = asyncio.Event()
        reply_received = asyncio.Event()
        writing = False
        service.thinking_voice = ThinkingVoice(delay=0.001)
        service.thinking_voice.clips = {PHRASES[0]: b"\x01\x00" * 48_000}
        original_receive = provider.receive

        async def receive():
            await filler_started.wait()
            event = await original_receive()
            reply_received.set()
            return event

        async def write(pcm):
            nonlocal writing
            assert not writing
            writing = True
            if pcm != answer:
                assert state.current == State.THINKING
                filler_started.set()
                await reply_received.wait()
                await asyncio.sleep(0.005)
            else:
                assert state.current == State.SPEAKING
            speaker.audio.append(pcm)
            writing = False

        provider.receive = receive
        speaker.write = write
        assert await asyncio.wait_for(service.run_turn(asyncio.Event()), 1)
        assert len(speaker.audio) == 2
        assert len(speaker.audio[0]) == CHUNK_BYTES
        assert speaker.audio[-1] == answer
        assert state.current == State.IDLE

    asyncio.run(exercise())


def test_provider_failure_stops_filler_and_waits_for_current_write():
    async def exercise():
        service, provider, speaker, _, state = make_service([])
        started = asyncio.Event()
        completed = asyncio.Event()
        service.thinking_voice = ThinkingVoice(delay=0.001)
        service.thinking_voice.clips = {PHRASES[0]: b"\x01\x00" * 48_000}

        async def write(pcm):
            started.set()
            await asyncio.sleep(0.01)
            completed.set()
            speaker.audio.append(pcm)

        async def receive():
            await started.wait()
            raise ProviderError("disconnected")

        speaker.write = write
        provider.receive = receive
        with pytest.raises(ProviderError, match="disconnected"):
            await asyncio.wait_for(service.run_turn(asyncio.Event()), 1)
        assert completed.is_set()
        assert len(speaker.audio) == 1
        assert state.current == State.ERROR
        assert not [task for task in asyncio.all_tasks() if task != asyncio.current_task()]

    asyncio.run(exercise())


def test_unavailable_synthesis_is_optional(monkeypatch):
    async def failed(phrase):
        raise RuntimeError("TTS unavailable")

    monkeypatch.setattr("cuty.audio.thinking.synthesize", failed)
    voice = ThinkingVoice()
    asyncio.run(voice.prepare())
    assert voice.choose() is None


def test_at_most_two_phrases_per_wait():
    class Speaker:
        def __init__(self):
            self.audio = []

        async def write(self, pcm):
            self.audio.append(pcm)

    voice = ThinkingVoice(delay=0.001, interval=0.001)
    voice.clips = {PHRASES[0]: b"\x01\x00"}
    speaker = Speaker()
    asyncio.run(voice.run(speaker, asyncio.Event()))
    assert len(speaker.audio) == 2
