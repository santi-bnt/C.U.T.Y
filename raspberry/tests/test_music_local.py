import asyncio
import wave

import pytest

from cuty.music.local import LocalMusicProvider


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
