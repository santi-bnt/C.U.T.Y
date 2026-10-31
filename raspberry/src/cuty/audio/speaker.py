"""Streaming speaker output behind a small interface."""

from __future__ import annotations

import asyncio
from typing import Protocol

from cuty.audio.devices import AudioDeviceError, _sounddevice
from cuty.audio.microphone import SAMPLE_RATE


class Speaker(Protocol):
    async def open(self) -> None: ...
    async def write(self, pcm16: bytes) -> None: ...
    async def close(self) -> None: ...


class SoundDeviceSpeaker:
    def __init__(self, device: int) -> None:
        self.device = device
        self._stream = None

    async def open(self) -> None:
        sd = _sounddevice()
        try:
            self._stream = sd.RawOutputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", device=self.device)
            self._stream.start()
        except (sd.PortAudioError, OSError) as exc:
            raise AudioDeviceError(f"Cannot open speaker: {exc}") from exc

    async def write(self, pcm16: bytes) -> None:
        if self._stream is None:
            raise AudioDeviceError("Speaker is not open.")
        sd = _sounddevice()
        try:
            await asyncio.to_thread(self._stream.write, pcm16)
        except (sd.PortAudioError, OSError, RuntimeError) as exc:
            raise AudioDeviceError(f"Speaker playback failed: {exc}") from exc

    async def close(self) -> None:
        if self._stream is not None:
            stream, self._stream = self._stream, None
            try:
                await asyncio.to_thread(stream.stop)
            finally:
                stream.close()
