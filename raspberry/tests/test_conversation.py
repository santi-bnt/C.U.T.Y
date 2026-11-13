import asyncio
import json

import pytest

from cuty.llm.provider import AIEvent, EventKind, ProviderError, ToolCall, WebSource
from cuty.brain.conversation import ConversationService
from cuty.brain.states import State, StateMachine
from cuty.face.expressions import Expression
from cuty.face.expression_sink import ExpressionController


class FakeMicrophone:
    async def chunks(self, stop):
        yield b"\x00\x00" * 480
        stop.set()


class FakeSpeaker:
    def __init__(self):
        self.audio = []

    async def open(self):
        pass

    async def write(self, pcm16):
        self.audio.append(pcm16)

    async def close(self):
        pass


class FakeSink:
    def __init__(self):
        self.events = []

    def set_expression(self, expression, intensity=1.0):
        self.events.append((expression, intensity))


class FakeProvider:
    def __init__(self, events):
        self.events = list(events)
        self.sent = []
        self.results = []
        self.continued = 0
        self.finished = 0

    async def connect(self):
        pass

    async def close(self):
        pass

    async def start_turn(self):
        self.sent.clear()

    async def send_audio(self, pcm16):
        self.sent.append(pcm16)

    async def finish_input(self):
        self.finished += 1

    async def receive(self):
        event = self.events.pop(0)
        if isinstance(event, Exception):
            raise event
        return event

    async def submit_tool_result(self, call_id, output):
        self.results.append((call_id, json.loads(output)))

    async def continue_response(self):
        self.continued += 1


def make_service(events):
    provider = FakeProvider(events)
    sink = FakeSink()
    expressions = ExpressionController(sink)
    state = StateMachine(expressions.on_state)
    speaker = FakeSpeaker()
    service = ConversationService(provider, FakeMicrophone(), speaker, state, expressions)
    return service, provider, speaker, sink, state


def test_music_voice_command_is_applied_locally_and_model_audio_is_discarded():
    from cuty.music.protocol import MusicTrack, PlaybackState

    service, provider, speaker, _, state = make_service([
        AIEvent(EventKind.AUDIO, audio=b"\x03\x00" * 64),
        AIEvent(EventKind.INPUT_TRANSCRIPT, transcript="Cuty, pon Come Together de The Beatles"),
        AIEvent(EventKind.DONE),
    ])

    class Music:
        def __init__(self):
            self.track = MusicTrack("local-id", "Come Together", "The Beatles")
            self.status = "stopped"
            self.played = []

        async def search_tracks(self, query):
            assert query == "come together de the beatles"
            return [self.track]

        async def play(self, track_id):
            self.played.append(track_id)
            self.status = "playing"

        async def get_playback_state(self):
            return PlaybackState(self.status, self.track if self.status != "stopped" else None, 70)

        async def pause(self): self.status = "paused"
        async def resume(self): self.status = "playing"
        async def stop(self): self.status = "stopped"
        async def next(self): self.status = "playing"
        async def previous(self): self.status = "playing"
        async def set_volume(self, _value): pass

    music = Music()
    service.music = music
    asyncio.run(service.run_turn(asyncio.Event()))

    assert music.played == ["local-id"]
    assert speaker.audio == []  # Gemini's generic reply was held and discarded.
    assert state.current == State.MUSIC_PLAYING


def test_multiturn_conversation_and_tool_expression():
    service, provider, speaker, sink, state = make_service([
        AIEvent(EventKind.DONE, tool_calls=(ToolCall("call1", "set_expression", '{"expression":"happy","intensity":0.8}'),)),
        AIEvent(EventKind.AUDIO, audio=b"\x00\x00" * 480),
        AIEvent(EventKind.TRANSCRIPT, transcript="Hello Santiago!"),
        AIEvent(EventKind.DONE),
        AIEvent(EventKind.AUDIO, audio=b"\x01\x00" * 480),
        AIEvent(EventKind.DONE),
    ])
    assert asyncio.run(service.run_turn(asyncio.Event()))
    assert asyncio.run(service.run_turn(asyncio.Event()))
    assert provider.finished == 2
    assert provider.continued == 1
    assert provider.results[0][1]["event"]["expression"] == "happy"
    assert len(speaker.audio) == 2
    assert state.current == State.IDLE
    assert (Expression.HAPPY, 0.8) in sink.events
    assert sink.events[-1][0] == Expression.IDLE


def test_voice_transcript_deterministically_dispatches_local_music_search():
    class Music:
        def __init__(self):
            self.status = "stopped"
            self.volume = 70
            self.played = []

        async def search_tracks(self, query):
            from cuty.music.protocol import MusicTrack
            assert query == "505 de arctic monkeys"
            return [MusicTrack("track-505", "505", "Arctic Monkeys")]

        async def play(self, track_id):
            self.played.append(track_id)
            self.status = "playing"

        async def get_playback_state(self):
            from cuty.music.protocol import PlaybackState
            track = None
            return PlaybackState(self.status, track, self.volume)

        async def pause(self): self.status = "paused"
        async def resume(self): self.status = "playing"
        async def stop(self): self.status = "stopped"
        async def next(self): self.status = "playing"
        async def previous(self): self.status = "playing"
        async def set_volume(self, value): self.volume = value

    service, _, _, _, state = make_service([
        AIEvent(EventKind.INPUT_TRANSCRIPT, transcript="Cuty, pon 505 de Arctic Monkeys"),
        AIEvent(EventKind.AUDIO, audio=b"\x00\x00" * 480),
        AIEvent(EventKind.DONE),
    ])
    music = Music()
    service.music = music
    assert asyncio.run(service.run_turn(asyncio.Event()))
    assert music.played == ["track-505"]
    assert state.current == State.MUSIC_PLAYING


def test_invalid_tool_arguments_are_rejected_and_reply_continues():
    service, provider, _, sink, state = make_service([
        AIEvent(EventKind.DONE, tool_calls=(ToolCall("bad", "set_expression", '{"expression":"speaking","intensity":2}'),)),
        AIEvent(EventKind.AUDIO, audio=b"\x00\x00" * 480),
        AIEvent(EventKind.DONE),
    ])
    asyncio.run(service.run_turn(asyncio.Event()))
    assert provider.results == [("bad", {"ok": False, "error": "Invalid expression arguments"})]
    assert state.current == State.IDLE
    assert (Expression.SPEAKING, 2) not in sink.events


def test_provider_error_enters_error_state():
    service, _, _, _, state = make_service([ProviderError("disconnected")])
    with pytest.raises(ProviderError, match="disconnected"):
        asyncio.run(service.run_turn(asyncio.Event()))
    assert state.current == State.ERROR
    state.set(State.IDLE)


def test_invalid_pcm_enters_error_state():
    service, _, _, _, state = make_service([AIEvent(EventKind.AUDIO, audio=b"\x00")])
    with pytest.raises(ProviderError, match="PCM16"):
        asyncio.run(service.run_turn(asyncio.Event()))
    assert state.current == State.ERROR


def test_tool_is_answered_while_speaker_is_still_playing():
    async def exercise():
        service, provider, speaker, _, _ = make_service([
            AIEvent(EventKind.AUDIO, audio=b"\x00\x00" * 480),
            AIEvent(EventKind.DONE, tool_calls=(ToolCall("call", "set_expression", '{"expression":"happy","intensity":0.8}'),)),
            AIEvent(EventKind.DONE),
        ])
        playback_started = asyncio.Event()
        release_playback = asyncio.Event()

        async def slow_write(pcm16):
            playback_started.set()
            await release_playback.wait()
            speaker.audio.append(pcm16)

        speaker.write = slow_write
        task = asyncio.create_task(service.run_turn(asyncio.Event()))
        try:
            await asyncio.wait_for(playback_started.wait(), 1)
            for _ in range(20):
                if provider.results:
                    break
                await asyncio.sleep(0)
            assert provider.results[0][0] == "call"
            assert not task.done()
            release_playback.set()
            assert await asyncio.wait_for(task, 1)
        finally:
            release_playback.set()
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    asyncio.run(exercise())


def test_silent_response_is_reported_instead_of_succeeding():
    service, _, _, _, state = make_service([AIEvent(EventKind.DONE)])
    with pytest.raises(ProviderError, match="sin enviar voz"):
        asyncio.run(service.run_turn(asyncio.Event()))
    assert state.current == State.ERROR


def test_first_audio_deadline_includes_transcripts_and_tool_events(monkeypatch):
    import cuty.brain.conversation as conversation

    monkeypatch.setattr(conversation, "RESPONSE_START_TIMEOUT", 0.03)
    service, provider, _, _, state = make_service([])

    async def keep_sending_non_audio():
        await asyncio.sleep(0.005)
        return AIEvent(EventKind.OTHER)

    provider.receive = keep_sending_non_audio
    with pytest.raises(ProviderError, match="no empezó a hablar"):
        asyncio.run(service.run_turn(asyncio.Event()))
    assert state.current == State.ERROR


def test_web_search_sources_are_logged_with_the_spoken_response(caplog):
    service, _, speaker, _, state = make_service([
        AIEvent(EventKind.WEB_SEARCH, search_queries=("Python latest release",),
                sources=(WebSource("Python", "https://www.python.org/downloads/"),)),
        AIEvent(EventKind.AUDIO, audio=b"\x00\x00" * 480),
        AIEvent(EventKind.DONE),
    ])
    with caplog.at_level("INFO"):
        asyncio.run(service.run_turn(asyncio.Event()))
    assert "Python latest release" in caplog.text
    assert "https://www.python.org/downloads/" in caplog.text
    assert len(speaker.audio) == 1
    assert state.current == State.IDLE


def test_search_tool_returns_actual_sources_to_voice_model(caplog):
    class FakeSearch:
        async def search(self, query):
            assert query == "Python release"
            return (WebSource("Python", "https://www.python.org/downloads/", "Latest version"),)

    service, provider, speaker, _, state = make_service([
        AIEvent(EventKind.DONE, tool_calls=(ToolCall("search1", "search_web", '{"query":"Python release"}'),)),
        AIEvent(EventKind.AUDIO, audio=b"\x00\x00" * 480),
        AIEvent(EventKind.DONE),
    ])
    service.web_search = FakeSearch()
    with caplog.at_level("INFO"):
        asyncio.run(service.run_turn(asyncio.Event()))
    result = provider.results[0][1]
    assert result["ok"] is True
    assert result["results"][0]["url"] == "https://www.python.org/downloads/"
    assert result["results"][0]["snippet"] == "Latest version"
    assert "https://www.python.org/downloads/" in caplog.text
    assert speaker.audio and state.current == State.IDLE


def test_failed_web_search_still_allows_a_spoken_explanation():
    from cuty.llm.web_search import WebSearchError

    class FailedSearch:
        async def search(self, query):
            raise WebSearchError("Buscador no disponible")

    service, provider, speaker, _, state = make_service([
        AIEvent(EventKind.DONE, tool_calls=(ToolCall("search1", "search_web", '{"query":"Python release"}'),)),
        AIEvent(EventKind.AUDIO, audio=b"\x00\x00" * 480),
        AIEvent(EventKind.DONE),
    ])
    service.web_search = FailedSearch()
    asyncio.run(service.run_turn(asyncio.Event()))
    assert provider.results == [("search1", {"ok": False, "error": "Buscador no disponible", "results": []})]
    assert speaker.audio and state.current == State.IDLE


def test_spoken_exit_is_normal_and_does_not_require_an_audio_reply():
    from cuty.brain.conversation import ReturnToMenu

    service, _, speaker, _, state = make_service([
        AIEvent(EventKind.INPUT_TRANSCRIPT, transcript="Quiero"),
        AIEvent(EventKind.INPUT_TRANSCRIPT, transcript="salir."),
        AIEvent(EventKind.DONE),
    ])
    service.voice_exit = True
    with pytest.raises(ReturnToMenu):
        asyncio.run(service.run_turn(asyncio.Event()))
    assert not speaker.audio and state.current == State.IDLE


def test_partial_exit_phrase_inside_a_longer_request_does_not_close():
    service, _, speaker, _, state = make_service([
        AIEvent(EventKind.INPUT_TRANSCRIPT, transcript="Quiero salir"),
        AIEvent(EventKind.INPUT_TRANSCRIPT, transcript="a caminar."),
        AIEvent(EventKind.AUDIO, audio=b"\x00\x00" * 480),
        AIEvent(EventKind.DONE),
    ])
    service.voice_exit = True
    asyncio.run(service.run_turn(asyncio.Event()))
    assert speaker.audio and state.current == State.IDLE


def test_model_menu_tool_ends_session_instead_of_continuing():
    from cuty.brain.conversation import ReturnToMenu

    service, provider, _, _, state = make_service([])
    service.voice_exit = True
    with pytest.raises(ReturnToMenu):
        asyncio.run(service._handle_tool(ToolCall("exit", "return_to_menu", '{}'),
                                         input_transcript="Cuty, quiero salir"))
    assert provider.results == [("exit", {"ok": True})]
    assert not provider.continued and state.current == State.IDLE


def test_model_cannot_close_menu_for_an_unrelated_transcription():
    service, provider, speaker, _, state = make_service([
        AIEvent(EventKind.INPUT_TRANSCRIPT, transcript="curiosarte"),
        AIEvent(EventKind.DONE, tool_calls=(ToolCall("exit", "return_to_menu", '{}'),)),
        AIEvent(EventKind.AUDIO, audio=b"\x00\x00" * 480), AIEvent(EventKind.DONE),
    ])
    service.voice_exit = True
    asyncio.run(service.run_turn(asyncio.Event()))
    assert not provider.results[0][1]["ok"]
    assert provider.continued == 1 and speaker.audio and state.current == State.IDLE


def test_keyboard_mode_does_not_exit_on_spoken_salir():
    service, _, speaker, _, state = make_service([
        AIEvent(EventKind.INPUT_TRANSCRIPT, transcript="Quiero salir."),
        AIEvent(EventKind.AUDIO, audio=b"\x00\x00" * 480),
        AIEvent(EventKind.DONE),
    ])
    asyncio.run(service.run_turn(asyncio.Event()))
    assert speaker.audio and state.current == State.IDLE


def test_send_failure_closes_microphone_before_leaving_conversation():
    closed = []

    class Microphone:
        async def chunks(self, stop):
            try:
                yield b"\x00\x00" * 320
                await asyncio.Event().wait()
            finally:
                closed.append(True)

    async def fail(pcm):
        raise ProviderError("Disconnected while recording")

    service, provider, _, _, state = make_service([])
    service.microphone = Microphone()
    service.half_duplex = True
    provider.send_audio = fail
    with pytest.raises(ProviderError, match="Disconnected while recording"):
        asyncio.run(service.run_turn(asyncio.Event()))
    assert closed == [True] and state.current == State.ERROR
