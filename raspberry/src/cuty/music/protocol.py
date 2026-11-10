"""Provider-neutral music playback contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class MusicTrack:
    id: str
    title: str
    artist: str = "Unknown artist"
    duration_seconds: float | None = None


@dataclass(frozen=True)
class PlaybackState:
    status: str
    track: MusicTrack | None
    volume: int
    position_seconds: float = 0.0


class MusicProvider(Protocol):
    async def search_tracks(self, query: str) -> list[MusicTrack]: ...
    async def get_track(self, track_id: str) -> MusicTrack | None: ...
    async def play(self, track_id: str) -> None: ...
    async def pause(self) -> None: ...
    async def resume(self) -> None: ...
    async def stop(self) -> None: ...
    async def next(self) -> None: ...
    async def previous(self) -> None: ...
    async def set_volume(self, value: int) -> None: ...
    async def get_playback_state(self) -> PlaybackState: ...
