"""Local file provider. Users must supply audio they are authorized to play."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Callable

from cuty.audio.speaker import Speaker
from cuty.music.protocol import MusicTrack, PlaybackState

SUPPORTED = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}


class LocalMusicProvider:
    """Decode a local library with PyAV and stream small PCM chunks to the robot speaker."""

    def __init__(self, speaker: Speaker, library: Path, *, volume: int = 70,
                 on_status: Callable[[str], None] | None = None) -> None:
        self.speaker = speaker
        self.library = library.expanduser().resolve()
        self.volume = max(0, min(100, int(volume)))
        self._tracks: list[MusicTrack] = []
        self._task: asyncio.Task | None = None
        self._resume_event = asyncio.Event()
        self._resume_event.set()
        self._status = "stopped"
        self._index = -1
        self._generation = 0
        self._write_lock = asyncio.Lock()
        self._on_status = on_status
        self._log = logging.getLogger("MUSIC")

    async def _scan(self) -> list[MusicTrack]:
        def scan() -> list[MusicTrack]:
            if not self.library.is_dir():
                return []
            return [MusicTrack(str(path), path.stem, "Local library")
                    for path in sorted(self.library.rglob("*"))
                    if path.is_file() and path.suffix.lower() in SUPPORTED]
        self._tracks = await asyncio.to_thread(scan)
        return self._tracks

    async def search_tracks(self, query: str) -> list[MusicTrack]:
        if not isinstance(query, str) or len(query) > 160:
            return []
        tracks = await self._scan()
        tokens = [part for part in query.casefold().split() if part]
        ranked = [(sum(token in f"{track.title} {track.artist}".casefold() for token in tokens), track)
                  for track in tracks]
        ranked = [(score, track) for score, track in ranked if score]
        return [track for _, track in sorted(ranked, key=lambda pair: (-pair[0], pair[1].title.casefold()))[:20]]

    async def get_track(self, track_id: str) -> MusicTrack | None:
        tracks = await self._scan()
        return next((track for track in tracks if track.id == track_id), None)

    async def play(self, track_id: str) -> None:
        track = await self.get_track(track_id)
        if track is None:
            raise ValueError("Track is not present in the configured local library.")
        await self.stop()
        self._index = next(i for i, item in enumerate(self._tracks) if item.id == track_id)
        self._set_status("playing")
        self._resume_event.set()
        generation = self._generation
        self._task = asyncio.create_task(self._play_file(track, generation), name="cuty-local-music")

    async def _play_file(self, track: MusicTrack, generation: int) -> None:
        try:
            import av

            container = await asyncio.to_thread(av.open, track.id)
            try:
                stream = next((item for item in container.streams if item.type == "audio"), None)
                if stream is None:
                    raise ValueError("Selected file contains no audio stream.")
                resampler = av.AudioResampler(format="s16", layout="mono", rate=24_000)
                for packet in container.demux(stream):
                    for frame in packet.decode():
                        for converted in resampler.resample(frame):
                            await self._wait_current(generation)
                            pcm = self._scale_pcm(bytes(converted.planes[0])[:converted.samples * 2])
                            await self._write(pcm, generation)
                for converted in resampler.resample(None):
                    await self._wait_current(generation)
                    pcm = self._scale_pcm(bytes(converted.planes[0])[:converted.samples * 2])
                    await self._write(pcm, generation)
            finally:
                container.close()
        except asyncio.CancelledError:
            raise
        except Exception:
            self._log.exception("Local playback failed for %s", track.title)
            self._set_status("error")
        else:
            if generation == self._generation and self._status == "playing":
                self._set_status("stopped")

    async def _wait_current(self, generation: int) -> None:
        if generation != self._generation:
            raise asyncio.CancelledError
        await self._resume_event.wait()
        if generation != self._generation:
            raise asyncio.CancelledError

    async def pause(self) -> None:
        if self._status == "playing":
            self._resume_event.clear()
            self._set_status("paused")
            async with self._write_lock:
                pass

    async def _write(self, pcm: bytes, generation: int) -> None:
        while True:
            await self._resume_event.wait()
            async with self._write_lock:
                if generation != self._generation:
                    raise asyncio.CancelledError
                if not self._resume_event.is_set() or self._status != "playing":
                    continue
                await self.speaker.write(pcm)
                return

    async def resume(self) -> None:
        if self._status == "paused":
            self._set_status("playing")
            self._resume_event.set()

    async def stop(self) -> None:
        task = self._task
        self._task = None
        self._generation += 1
        self._set_status("stopped")
        self._index = -1
        self._resume_event.set()
        if task and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    async def next(self) -> None:
        if not self._tracks:
            await self._scan()
        if self._tracks:
            await self.play(self._tracks[(self._index + 1) % len(self._tracks)].id)

    async def previous(self) -> None:
        if not self._tracks:
            await self._scan()
        if self._tracks:
            await self.play(self._tracks[max(0, self._index - 1)].id)

    async def set_volume(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
            raise ValueError("Volume must be an integer from 0 to 100.")
        self.volume = value

    def _scale_pcm(self, pcm: bytes) -> bytes:
        if self.volume == 100 or not pcm:
            return pcm
        import array
        samples = array.array("h")
        samples.frombytes(pcm)
        gain = self.volume / 100
        for index, sample in enumerate(samples):
            samples[index] = max(-32768, min(32767, round(sample * gain)))
        return samples.tobytes()

    async def get_playback_state(self) -> PlaybackState:
        track = self._tracks[self._index] if 0 <= self._index < len(self._tracks) else None
        return PlaybackState(self._status, track, self.volume)

    async def wait_until_finished(self) -> None:
        """Let hands-free mode keep the song audible instead of immediately reopening its mic."""
        task = self._task
        if task is not None:
            await asyncio.shield(task)

    async def close(self) -> None:
        await self.stop()

    def _set_status(self, status: str) -> None:
        if status == self._status:
            return
        self._status = status
        if self._on_status is not None:
            try:
                self._on_status(status)
            except Exception:
                self._log.exception("Playback status callback failed")
