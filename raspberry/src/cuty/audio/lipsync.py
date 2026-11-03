"""Lip sync: a speaker wrapper that tells the face how loud C.U.T.Y is talking.

Every PCM chunk written to the speaker is cut into 20 ms windows and their
loudness is placed on a playback timeline. A background task sends the level
that is *actually audible now* to the face ~30 times per second, so the mouth
opens on syllables instead of when the network delivers audio. It wraps both
the AI's reply and the "thinking" asides, since both go through the speaker.

Environment:
    CUTY_LIPSYNC_DELAY  seconds of extra output latency to compensate (default 0.08)
"""

from __future__ import annotations

import asyncio
import math
import os
import sys
import time
from collections import deque

from cuty.audio.microphone import SAMPLE_RATE
from cuty.audio.speaker import Speaker

WINDOW = 0.02
QUIET_DB = -48.0   # at or below: mouth closed
LOUD_DB = -12.0    # at or above: mouth fully open


def level_of(samples) -> float:
    """Mouth opening 0..1 for one window of int16 samples (dBFS mapped)."""
    n = len(samples)
    if n == 0:
        return 0.0
    rms = math.sqrt(sum(v * v for v in samples) / n)
    if rms < 1.0:
        return 0.0
    db = 20.0 * math.log10(rms / 32768.0)
    return min(1.0, max(0.0, (db - QUIET_DB) / (LOUD_DB - QUIET_DB)))


def envelope(pcm16: bytes, sample_rate: int = SAMPLE_RATE, window: float = WINDOW) -> list[float]:
    """Loudness per window for little-endian mono PCM16."""
    if len(pcm16) % 2:
        pcm16 = pcm16[:-1]
    samples = memoryview(pcm16).cast("h")
    if sys.byteorder != "little":
        import array

        swapped = array.array("h", pcm16)
        swapped.byteswap()
        samples = memoryview(swapped)
    size = max(1, int(sample_rate * window))
    return [level_of(samples[i:i + size]) for i in range(0, len(samples), size)]


class LipSyncSpeaker:
    """``Speaker`` that also drives the face's mouth through a link."""

    def __init__(self, speaker: Speaker, link, *, sample_rate: int = SAMPLE_RATE,
                 rate: float = 30.0, delay: float | None = None, clock=time.monotonic) -> None:
        self.speaker = speaker
        self.link = link
        self.sample_rate = sample_rate
        self.period = 1.0 / rate
        self.delay = float(os.getenv("CUTY_LIPSYNC_DELAY", "0.08")) if delay is None else delay
        self._clock = clock
        self._timeline: deque[tuple[float, float]] = deque()
        self._end = 0.0
        self._task: asyncio.Task | None = None
        self._last_sent: float | None = None

    async def open(self) -> None:
        await self.speaker.open()
        self._task = asyncio.create_task(self._feed())

    async def write(self, pcm16: bytes) -> None:
        self.schedule(pcm16)
        await self.speaker.write(pcm16)

    def schedule(self, pcm16: bytes) -> None:
        """Put a chunk's loudness on the playback timeline."""
        now = self._clock()
        start = max(now, self._end)
        levels = envelope(pcm16, self.sample_rate)
        for i, level in enumerate(levels):
            self._timeline.append((start + i * WINDOW, level))
        self._end = start + (len(pcm16) // 2) / self.sample_rate

    def level_now(self) -> float:
        """Loudest window that became audible since the previous call."""
        audible = self._clock() - self.delay
        level = None
        while self._timeline and self._timeline[0][0] <= audible:
            _, value = self._timeline.popleft()
            level = value if level is None else max(level, value)
        if level is not None:
            return level
        if audible >= self._end:
            return 0.0
        return self._last_sent or 0.0

    def tick(self) -> None:
        level = self.level_now()
        if level > 0.0 or self._last_sent != 0.0:
            self.link.mouth(level)
        self._last_sent = level

    async def _feed(self) -> None:
        while True:
            self.tick()
            await asyncio.sleep(self.period)

    async def close(self) -> None:
        if self._task is not None:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None
        self._timeline.clear()
        self.link.mouth(0.0)
        await self.speaker.close()
