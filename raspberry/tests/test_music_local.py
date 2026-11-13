import asyncio
import wave

import pytest

from cuty.music.local import LocalMusicProvider
from cuty.music.protocol import MusicTrack


class FakeSpeaker:
    def __init__(self):
        self.chunks = []

    async def open(self):
        pass

    async def write(self, pcm):
        self.chunks.append(pcm)

    async def close(self):
        pass


def make_wav(path):
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(24000)
        output.writeframes(b"\x10\x00" * 2400)


def test_local_library_search_and_async_playback(tmp_path):
    make_wav(tmp_path / "505 - Arctic Monkeys.wav")
    (tmp_path / "notes.txt").write_text("not audio")
    speaker = FakeSpeaker()
    provider = LocalMusicProvider(speaker, tmp_path)

    async def exercise():
        matches = await provider.search_tracks("505 Arctic Monkeys")
        assert len(matches) == 1
        assert matches[0].title == "505 - Arctic Monkeys"
        await provider.play(matches[0].id)
        await asyncio.wait_for(provider._task, timeout=3)
        return matches[0], await provider.get_playback_state()

    track, state = asyncio.run(exercise())
    assert state.status == "stopped"
    assert state.track == track
    assert speaker.chunks


def test_volume_is_bounded(tmp_path):
    provider = LocalMusicProvider(FakeSpeaker(), tmp_path)
    async def exercise():
        with pytest.raises(ValueError):
            await provider.set_volume(101)
        await provider.set_volume(30)
        return await provider.get_playback_state()
    assert asyncio.run(exercise()).volume == 30
    assert provider._scale_pcm(b"\x10\x00") == b"\x05\x00"


def test_next_and_current_track_state(tmp_path):
    make_wav(tmp_path / "01.wav")
    make_wav(tmp_path / "02.wav")
    provider = LocalMusicProvider(FakeSpeaker(), tmp_path)

    async def exercise():
        await provider.search_tracks("01")
        await provider.play(provider._tracks[0].id)
        await provider.next()
        state = await provider.get_playback_state()
        assert state.status == "playing"
        assert state.track.title == "02"
        await provider.close()

    asyncio.run(exercise())


def test_pause_resume_and_stop_control_the_live_decoder(tmp_path):
    def long_wav(path):
        with wave.open(str(path), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(24000)
            output.writeframes(b"\x10\x00" * 24000 * 10)

    class PacedSpeaker(FakeSpeaker):
        async def write(self, pcm):
            await asyncio.sleep(0.005)
            await super().write(pcm)

    track_path = tmp_path / "long.wav"
    long_wav(track_path)
    speaker = PacedSpeaker()
    provider = LocalMusicProvider(speaker, tmp_path)

    async def exercise():
        tracks = await provider.search_tracks("long")
        await provider.play(tracks[0].id)
        await asyncio.sleep(0.03)
        await provider.pause()
        paused_count = len(speaker.chunks)
        assert (await provider.get_playback_state()).status == "paused"
        await asyncio.sleep(0.03)
        assert len(speaker.chunks) == paused_count
        await provider.resume()
        await asyncio.sleep(0.03)
        assert len(speaker.chunks) > paused_count
        await provider.stop()
        assert (await provider.get_playback_state()).status == "stopped"
        assert provider._task is None

    asyncio.run(exercise())


def test_auto_advance_and_wait_until_finished_cover_the_whole_queue(tmp_path):
    make_wav(tmp_path / "01.wav")
    make_wav(tmp_path / "02.wav")
    speaker = FakeSpeaker()
    provider = LocalMusicProvider(speaker, tmp_path)

    async def exercise():
        tracks = await provider.search_tracks("01")
        await provider.play(tracks[0].id)
        await asyncio.wait_for(provider.wait_until_finished(), timeout=3)
        state = await provider.get_playback_state()
        assert state.status == "stopped"
        assert state.track.title == "02"
        assert len(speaker.chunks) >= 2

    asyncio.run(exercise())


def test_metadata_tags_are_used_without_changing_filename_fallback(tmp_path, monkeypatch):
    path = tmp_path / "random-name.mp3"
    path.write_bytes(b"test")
    speaker = FakeSpeaker()
    provider = LocalMusicProvider(speaker, tmp_path)
    monkeypatch.setattr(provider, "_read_track", lambda file: MusicTrack(
        str(file), "Come Together", "The Beatles", 259.0
    ))

    async def exercise():
        tracks = await provider.search_tracks("come together de the beatles")
        assert len(tracks) == 1
        assert tracks[0].title == "Come Together"
        assert tracks[0].artist == "The Beatles"
        assert tracks[0].duration_seconds == 259.0

    asyncio.run(exercise())


def test_decoder_error_is_reported_and_close_stops_provider(tmp_path):
    (tmp_path / "broken.wav").write_bytes(b"not a wav file")
    provider = LocalMusicProvider(FakeSpeaker(), tmp_path)

    async def exercise():
        tracks = await provider.search_tracks("broken")
        await provider.play(tracks[0].id)
        await asyncio.wait_for(provider.wait_until_finished(), timeout=3)
        assert (await provider.get_playback_state()).status == "error"
        await provider.close()
        assert (await provider.get_playback_state()).status == "stopped"
        assert provider._task is None

    asyncio.run(exercise())
