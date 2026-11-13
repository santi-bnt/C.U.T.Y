"""Software PCM volume for the assistant voice, independent of ALSA gain."""

from __future__ import annotations

import array
import os


def _level(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
        raise ValueError("Volume must be an integer from 0 to 100.")
    return value


class VoiceVolume:
    def __init__(self, value: int = 70, step: int = 10) -> None:
        self.value = _level(value)
        self.step = _level(step)
        if self.step == 0:
            raise ValueError("Volume step must be from 1 to 100.")
        self._before_mute = self.value if self.value else 70
        self.muted = self.value == 0

    @classmethod
    def from_env(cls) -> "VoiceVolume":
        try:
            value = int(os.getenv("CUTY_VOICE_VOLUME", "70"))
            step = int(os.getenv("CUTY_VOLUME_STEP", "10"))
            return cls(value, step)
        except ValueError as exc:
            raise ValueError("CUTY_VOICE_VOLUME and CUTY_VOLUME_STEP must be integers in 0..100 (step 1..100).") from exc

    def set(self, value: int) -> int:
        value = _level(value)
        if value:
            self._before_mute = value
            self.muted = False
        else:
            self.mute()
        self.value = value
        return self.value

    def adjust(self, delta: int) -> int:
        if isinstance(delta, bool) or not isinstance(delta, int):
            raise ValueError("Volume adjustment must be an integer.")
        return self.set(max(0, min(100, self.value + delta)))

    def mute(self) -> int:
        if self.value > 0:
            self._before_mute = self.value
        self.value = 0
        self.muted = True
        return self.value

    def unmute(self) -> int:
        if self.muted or self.value == 0:
            self.value = self._before_mute or 70
        self.muted = False
        return self.value

    def apply(self, pcm16: bytes) -> bytes:
        if len(pcm16) % 2:
            raise ValueError("Speaker received incomplete PCM16 samples.")
        if self.value == 100 or not pcm16:
            return pcm16
        if self.value == 0:
            return bytes(len(pcm16))
        samples = array.array("h")
        samples.frombytes(pcm16)
        gain = self.value / 100
        for index, sample in enumerate(samples):
            samples[index] = max(-32768, min(32767, round(sample * gain)))
        return samples.tobytes()


class VolumeSpeaker:
    """Speaker decorator: applies voice-only software gain at playback time."""

    def __init__(self, speaker, volume: VoiceVolume) -> None:
        self.speaker = speaker
        self.volume = volume

    async def open(self) -> None:
        await self.speaker.open()

    async def write(self, pcm16: bytes) -> None:
        await self.speaker.write(self.volume.apply(pcm16))

    async def close(self) -> None:
        await self.speaker.close()
