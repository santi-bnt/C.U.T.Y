"""Streaming speaker output behind a small interface."""

from __future__ import annotations

import asyncio
import logging
from array import array
from typing import Protocol

from cuty.audio.devices import AudioDeviceError, _sounddevice, open_output_stream
from cuty.audio.microphone import SAMPLE_RATE


class Speaker(Protocol):
    async def open(self) -> None: ...
    async def write(self, pcm16: bytes) -> None: ...
    async def close(self) -> None: ...


class OutputPCM:
    """Keep provider audio at 24 kHz, converting only at the hardware boundary."""

    def __init__(self, rate: int, channels: int) -> None:
        self.channels = channels
        self.resampler = None
        if rate != SAMPLE_RATE:
            import av

            self.resampler = av.AudioResampler(format="s16", layout="mono", rate=rate)

    def _channels(self, pcm: bytes) -> bytes:
        if self.channels == 1:
            return pcm
        return array("h", (v for sample in array("h", pcm) for v in (sample, sample))).tobytes()

    def _frames(self, frames) -> bytes:
        pcm = b"".join(bytes(frame.planes[0])[:frame.samples * 2] for frame in frames)
        return self._channels(pcm)

    def convert(self, pcm: bytes) -> bytes:
        if len(pcm) % 2:
            raise AudioDeviceError("Speaker received incomplete PCM16 samples.")
        if not pcm:
            return b""
        if self.resampler is None:
            return self._channels(pcm)
        import av

        frame = av.AudioFrame(format="s16", layout="mono", samples=len(pcm) // 2)
        frame.sample_rate = SAMPLE_RATE
        frame.planes[0].update(pcm)
        return self._frames(self.resampler.resample(frame))

    def flush(self) -> bytes:
        return self._frames(self.resampler.resample(None)) if self.resampler is not None else b""


class SoundDeviceSpeaker:
    def __init__(self, device: int) -> None:
        self.device = device
        self._stream = None
        self._pcm = None

    async def open(self) -> None:
        try:
            self._stream, rate, channels = open_output_stream(self.device)
            self._pcm = OutputPCM(rate, channels)
            logging.getLogger("AUDIO").info("Salida física: %d Hz, %d canal(es); voz: %d Hz", rate, channels, SAMPLE_RATE)
        except Exception:
            if self._stream is not None:
                self._stream.close()
                self._stream = None
            raise

    async def write(self, pcm16: bytes) -> None:
        if self._stream is None:
            raise AudioDeviceError("Speaker is not open.")
        sd = _sounddevice()
        try:
            payload = self._pcm.convert(pcm16)
            if payload:
                await asyncio.to_thread(self._stream.write, payload)
        except (sd.PortAudioError, OSError, RuntimeError) as exc:
            raise AudioDeviceError(f"Speaker playback failed: {exc}") from exc

    async def close(self) -> None:
        if self._stream is not None:
            stream, self._stream = self._stream, None
            try:
                tail = self._pcm.flush() if self._pcm is not None else b""
                if tail:
                    await asyncio.to_thread(stream.write, tail)
            finally:
                self._pcm = None
                try:
                    await asyncio.to_thread(stream.stop)
                finally:
                    stream.close()
