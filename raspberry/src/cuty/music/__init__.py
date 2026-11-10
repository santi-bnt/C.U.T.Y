"""Local music playback and provider contracts."""

from cuty.music.local import LocalMusicProvider
from cuty.music.protocol import MusicProvider, MusicTrack, PlaybackState

__all__ = ["LocalMusicProvider", "MusicProvider", "MusicTrack", "PlaybackState"]
