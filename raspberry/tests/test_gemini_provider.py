import asyncio
import json

import pytest
from google.genai import types

from cuty.llm.gemini_provider import GeminiLiveProvider, _CONFIG
from cuty.llm.provider import EventKind


class FakeSession:
    def __init__(self):
        self.sent = []
        self.tool_results = []

    async def send_realtime_input(self, **kwargs):
        self.sent.append(kwargs)

    async def send_tool_response(self, *, function_responses):
        self.tool_results.extend(function_responses)

    async def receive(self):
        yield types.LiveServerMessage(tool_call=types.LiveServerToolCall(function_calls=[
            types.FunctionCall(id="call-1", name="set_expression", args={"expression": "happy", "intensity": 0.8})
        ]))
        yield types.LiveServerMessage(server_content=types.LiveServerContent(
            model_turn=types.Content(parts=[types.Part(inline_data=types.Blob(data=b"\x00\x00", mime_type="audio/pcm"))]),
            input_transcription=types.Transcription(text="Mi nombre es Santiago"),
            output_transcription=types.Transcription(text="Hola"),
            turn_complete=True,
        ))


def test_gemini_config_and_provider_turn_without_network():
    config = types.LiveConnectConfig(**_CONFIG)
    assert config.realtime_input_config.automatic_activity_detection.disabled
    assert config.input_audio_transcription is not None
    assert config.tools[0].function_declarations[0].name == "set_expression"
    assert config.tools[0].function_declarations[0].behavior == types.Behavior.BLOCKING
    assert config.tools[0].function_declarations[1].name == "search_web"
    assert config.tools[0].function_declarations[1].behavior == types.Behavior.BLOCKING

    provider = GeminiLiveProvider("fake-key")
    session = FakeSession()
    provider._session = session

    async def exercise():
        await provider.start_turn()
        await provider.send_audio(b"\x00\x00")
        await provider.finish_input()
        call = await provider.receive()
        assert call.kind == EventKind.DONE
        assert call.tool_calls[0].name == "set_expression"
        await provider.submit_tool_result("call-1", json.dumps({"ok": True}))
        await provider.continue_response()
        audio = await provider.receive()
        text = await provider.receive()
        heard = await provider.receive()
        done = await provider.receive()
        assert audio.kind == EventKind.AUDIO and audio.audio == b"\x00\x00"
        assert text.kind == EventKind.TRANSCRIPT and text.transcript == "Hola"
        assert heard.kind == EventKind.INPUT_TRANSCRIPT and heard.transcript == "Mi nombre es Santiago"
        assert done.kind == EventKind.DONE

    asyncio.run(exercise())
    assert isinstance(session.sent[0]["activity_start"], types.ActivityStart)
    assert session.sent[1]["audio"].mime_type == "audio/pcm;rate=16000"
    assert isinstance(session.sent[2]["activity_end"], types.ActivityEnd)
    assert session.tool_results[0].response == {"ok": True}


def test_gemini_provider_fails_fast_on_invalid_key(monkeypatch):
    from cuty.llm.provider import ProviderError

    class FakeClient:
        class aio:
            class live:
                @staticmethod
                def connect(model, config):
                    class FakeManager:
                        async def __aenter__(self):
                            class DummyError(Exception):
                                code = 1007
                            raise DummyError("1007 None. API key not valid. Please pass a valid API key.")

                        async def __aexit__(self, *args):
                            pass
                    return FakeManager()

    provider = GeminiLiveProvider("fake-invalid-key")
    provider._client = FakeClient()

    with pytest.raises(ProviderError) as exc_info:
        asyncio.run(provider.connect())
    assert "API key not valid" in str(exc_info.value)


def test_manual_activity_boundaries_are_sent_once_per_nonempty_turn():
    provider = GeminiLiveProvider("fake-key")
    session = FakeSession()
    provider._session = session

    async def exercise():
        await provider.start_turn()
        await provider.finish_input()
        assert session.sent == []
        for _ in range(2):
            await provider.start_turn()
            await provider.send_audio(b"\x00\x00")
            await provider.send_audio(b"\x01\x00")
            await provider.finish_input()
            await provider.finish_input()

    asyncio.run(exercise())
    assert [list(message)[0] for message in session.sent] == [
        "activity_start", "audio", "audio", "activity_end",
        "activity_start", "audio", "audio", "activity_end",
    ]


def test_grounded_search_sources_are_emitted_before_done_and_deduplicated_per_turn():
    provider = GeminiLiveProvider("fake-key")
    metadata = types.GroundingMetadata(
        web_search_queries=["Python release", "Python release", "  "],
        grounding_chunks=[
            {"web": {"title": "Python\nDownloads", "uri": "https://www.python.org/downloads/"}},
            {"web": {"title": "Duplicate", "uri": "https://www.python.org/downloads/"}},
            {"web": {"title": "Invalid", "uri": "javascript:alert(1)"}},
        ],
    )
    provider._queue_message(types.LiveServerMessage(server_content=types.LiveServerContent(
        grounding_metadata=metadata, turn_complete=True,
    )))
    search = provider._pending.popleft()
    assert search.kind == EventKind.WEB_SEARCH
    assert search.search_queries == ("Python release",)
    assert len(search.sources) == 1
    assert search.sources[0].title == "Python Downloads"
    assert search.sources[0].url == "https://www.python.org/downloads/"
    assert provider._pending.popleft().kind == EventKind.DONE
    provider._queue_search(metadata)
    assert not provider._pending
    asyncio.run(provider.start_turn())
    provider._queue_search(metadata)
    assert provider._pending.popleft().kind == EventKind.WEB_SEARCH
