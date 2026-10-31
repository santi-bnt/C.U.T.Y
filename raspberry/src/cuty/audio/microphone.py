"""20 ms mono PCM16 microphone chunks at the selected provider's input rate."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, Protocol

from cuty.audio.devices import AudioDeviceError, _sounddevice

SAMPLE_RATE = 24_000


class Microphone(Protocol):
    async def chunks(self, stop: asyncio.Event) -> AsyncIterator[bytes]: ...


class SoundDeviceMicrophone:
    def __init__(self, device: int, sample_rate: int = SAMPLE_RATE) -> None:
        self.device = device
        self.sample_rate = sample_rate

    async def chunks(self, stop: asyncio.Event) -> AsyncIterator[bytes]:
        sd = _sounddevice()
        chunk_frames = self.sample_rate // 50
        try:
            with sd.RawInputStream(samplerate=self.sample_rate, channels=1, dtype="int16", device=self.device, blocksize=chunk_frames) as stream:
                while not stop.is_set():
                    data, overflowed = await asyncio.to_thread(stream.read, chunk_frames)
                    if overflowed:
                        raise AudioDeviceError("Microphone overflowed. Try another input device or close other audio apps.")
                    yield bytes(data)
        except (sd.PortAudioError, OSError) as exc:
            raise AudioDeviceError(f"Cannot record from microphone: {exc}") from exc
