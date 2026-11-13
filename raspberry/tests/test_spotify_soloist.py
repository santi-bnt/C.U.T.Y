import asyncio
import logging

import pytest

from cuty.music.spotify_soloist import SpotifySoloistProvider
from cuty.music.spotify_soloist import SpotifySoloistError


class Response:
    def raise_for_status(self):
        pass

    def json(self):
        return {"tracks": {"items": [{
            "uri": "spotify:track:abc", "name": "505",
            "artists": [{"name": "Arctic Monkeys"}], "duration_ms": 253000,
        }]}}


def make_provider():
    provider = SpotifySoloistProvider(
        "ws://127.0.0.1:9090", "client-id", "client-secret", market="MX"
    )
    return provider


def test_spotify_search_returns_catalog_uris_and_metadata(monkeypatch):
    provider = make_provider()
    async def token(): return "token"
    async def get(*args, **kwargs): return Response()
    monkeypatch.setattr(provider, "_token", token)
    monkeypatch.setattr(provider._http, "get", get)

    async def exercise():
        tracks = await provider.search_tracks("505 de Arctic Monkeys")
        assert tracks[0].id == "spotify:track:abc"
        assert tracks[0].artist == "Arctic Monkeys"
        assert tracks[0].duration_seconds == 253
        assert await provider.get_track(tracks[0].id) == tracks[0]
        await provider.close()

    asyncio.run(exercise())


def test_play_controls_only_soloist_uri_and_volume_bounds(monkeypatch):
    provider = make_provider()
    commands = []
    async def request(command, **fields): commands.append((command, fields)); return {}
    monkeypatch.setattr(provider, "_request", request)

    async def exercise():
        await provider.play("spotify:track:abc")
        with pytest.raises(ValueError):
            await provider.play("https://example.com/audio.mp3")
        with pytest.raises(ValueError):
            await provider.set_volume(101)
        await provider.set_volume(35)
        assert commands == [
            ("play", {"uri": "spotify:track:abc"}),
            ("set_volume", {"volume": 35}),
        ]
        await provider.close()

    asyncio.run(exercise())


def test_playback_snapshot_maps_now_playing_and_soloist_errors(monkeypatch):
    provider = make_provider()
    payload = {
        "status": "playing", "is_active": True, "volume": 42,
        "position": {"position_ms": 12000},
        "item": {"uri": "spotify:track:abc", "decorations": {
            "identity": {"name": "505"},
            "creators": [{"entity": {"decorations": {"identity": {"name": "Arctic Monkeys"}}}}],
            "playback": {"duration_ms": 253000},
        }},
    }
    async def request(command, **fields): return payload
    monkeypatch.setattr(provider, "_request", request)

    async def exercise():
        state = await provider.get_playback_state()
        assert state.status == "playing"
        assert state.track.title == "505"
        assert state.track.artist == "Arctic Monkeys"
        assert state.position_seconds == 12
        assert state.volume == 42
        await provider.close()

    asyncio.run(exercise())


def test_soloist_must_bind_loopback():
    with pytest.raises(ValueError):
        SpotifySoloistProvider("ws://0.0.0.0:9090", "id", "secret")


def test_offline_soloist_reports_stopped_without_breaking_voice_mode(monkeypatch):
    provider = make_provider()
    async def request(*args, **kwargs):
        raise SpotifySoloistError("offline")
    monkeypatch.setattr(provider, "_request", request)

    async def exercise():
        state = await provider.get_playback_state()
        assert (state.status, state.track) == ("stopped", None)
        await provider.close()

    asyncio.run(exercise())


def test_external_playback_starts_only_after_voice_stream_closes():
    from cuty.brain.conversation import ConversationService
    from cuty.brain.states import State, StateMachine
    from cuty.music.protocol import PlaybackState

    events = []

    class Speaker:
        async def close(self): events.append("speaker_closed")

    class Music:
        external_output = True
        async def play(self, track_id): events.append(("play", track_id))
        async def get_playback_state(self):
            return PlaybackState("playing", None, 70)

    service = object.__new__(ConversationService)
    service.music = Music()
    service.speaker = Speaker()
    service.state = StateMachine()
    service._deferred_music_action = ("play", "spotify:track:abc")
    service._log = logging.getLogger("test")

    async def exercise():
        await service._start_deferred_music_action(False)
        assert service.state.current == State.MUSIC_PLAYING
        assert events == ["speaker_closed", ("play", "spotify:track:abc")]

    asyncio.run(exercise())
