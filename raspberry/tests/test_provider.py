import asyncio
import base64
from types import SimpleNamespace

import pytest

from cuty.llm.openai_provider import OpenAIRealtimeProvider
from cuty.llm.provider import EventKind, ProviderError


class FakeBuffer:
    def __init__(self):
        self.calls = []

    async def clear(self):
        self.calls.append("clear")

    async def append(self, *, audio):
        self.calls.append(("append", audio))

    async def commit(self):
        self.calls.append("commit")


class FakeResponse:
    def __init__(self):
        self.created = 0

    async def create(self):
        self.created += 1


class FakeConnection:
    def __init__(self, events):
        self.events = list(events)
        self.input_audio_buffer = FakeBuffer()
        self.response = FakeResponse()

    async def recv(self):
        return self.events.pop(0)


def test_provider_audio_api_and_normalization():
    provider = OpenAIRealtimeProvider("fake-key")
    conn = FakeConnection([
        SimpleNamespace(type="response.output_audio.delta", delta=base64.b64encode(b"\x00\x00").decode()),
        SimpleNamespace(type="response.done", response=SimpleNamespace(status="completed", output=[
            SimpleNamespace(type="function_call", call_id="c1", name="set_expression", arguments="{}")
        ])),
    ])
    provider._connection = conn

    async def exercise():
        await provider.start_turn()
        await provider.send_audio(b"\x00\x00")
        await provider.finish_input()
        first = await provider.receive()
        second = await provider.receive()
        assert first.kind == EventKind.AUDIO and first.audio == b"\x00\x00"
        assert second.kind == EventKind.DONE and second.tool_calls[0].call_id == "c1"
        assert conn.input_audio_buffer.calls == ["clear", ("append", "AAA="), "commit"]
        assert conn.response.created == 1

    asyncio.run(exercise())


def test_malformed_provider_audio_is_clean_error():
    provider = OpenAIRealtimeProvider("fake-key")
    provider._connection = FakeConnection([SimpleNamespace(type="response.output_audio.delta", delta="!")])
    with pytest.raises(ProviderError, match="malformed audio"):
        asyncio.run(provider.receive())


def test_session_configuration_uses_manual_turns_and_expression_tool():
    provider = OpenAIRealtimeProvider("fake-key")
    configured = []

    class Session:
        async def update(self, *, session):
            configured.append(session)

    class Connection:
        session = Session()

        async def recv(self):
            return SimpleNamespace(type="session.updated")

        async def close(self):
            pass

    class Manager:
        async def enter(self):
            return Connection()

    class Realtime:
        def connect(self, *, model, max_retries):
            assert model == "gpt-realtime-2.1" and max_retries == 0
            return Manager()

    class Client:
        realtime = Realtime()

        async def close(self):
            pass

    provider._client = Client()
    asyncio.run(provider.connect())
    session = configured[0]
    assert session["audio"]["input"]["turn_detection"] is None
    assert session["output_modalities"] == ["audio"]
    assert session["tools"][0]["name"] == "set_expression"
    asyncio.run(provider.close())


def test_server_error_redacts_key():
    provider = OpenAIRealtimeProvider("fake-key")
    provider._connection = FakeConnection([
        SimpleNamespace(type="error", error=SimpleNamespace(code="bad", message="invalid fake-key"))
    ])
    with pytest.raises(ProviderError) as exc:
        asyncio.run(provider.receive())
    assert "fake-key" not in str(exc.value)
