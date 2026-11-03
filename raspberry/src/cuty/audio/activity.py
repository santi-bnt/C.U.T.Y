"""Local speech boundaries for hands-free turns, without extra dependencies."""

from __future__ import annotations

import asyncio
import math
import os
from array import array
from collections import deque
from contextlib import aclosing

from cuty.audio.microphone import Microphone


class SpeechMicrophone:
    """Wait locally for speech, retain its onset, and stop after a silent pause.

    The underlying microphone is opened only while listening, preventing the
    robot's own greeting/reply from becoming a new question. This is energy
    detection, not speech recognition or acoustic echo cancellation.
    """

    def __init__(self, microphone: Microphone, sample_rate: int, *, threshold: float = 350,
                 silence: float = 0.9, minimum: float = 0.12, maximum: float = 20) -> None:
        if (not all(math.isfinite(v) and v > 0 for v in (threshold, silence, minimum, maximum))
                or threshold > 32768 or minimum >= maximum):
            raise ValueError("Invalid speech threshold or timing.")
        self.microphone = microphone
        self.sample_rate = sample_rate
        self.threshold, self.silence = threshold, silence
        self.minimum, self.maximum = minimum, maximum

    @classmethod
    def from_env(cls, microphone: Microphone, sample_rate: int) -> SpeechMicrophone:
        return cls(microphone, sample_rate,
                   threshold=float(os.getenv("CUTY_VAD_THRESHOLD", "350")),
                   silence=float(os.getenv("CUTY_VAD_SILENCE", "0.9")))

    async def chunks(self, stop: asyncio.Event):
        pre_roll = deque()
        buffered = loud = quiet = elapsed = 0.0
        started = False
        async with aclosing(self.microphone.chunks(stop)) as source:
            async for pcm in source:
                samples = array("h", pcm)
                duration = len(samples) / self.sample_rate
                if not samples:
                    continue
                rms = math.sqrt(sum(value * value for value in samples) / len(samples))
                voiced = rms >= self.threshold
                if not started:
                    pre_roll.append((pcm, duration))
                    buffered += duration
                    while pre_roll and buffered - pre_roll[0][1] > 0.3:
                        buffered -= pre_roll.popleft()[1]
                    loud = loud + duration if voiced else 0.0
                    if loud + 1e-9 < self.minimum:
                        continue
                    started = True
                    for chunk, _ in pre_roll:
                        yield chunk
                    pre_roll.clear()
                else:
                    yield pcm
                elapsed += duration
                quiet = 0.0 if voiced else quiet + duration
                if quiet + 1e-9 >= self.silence or elapsed + 1e-9 >= self.maximum:
                    stop.set()
                    return
