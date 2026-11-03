"""Local speech boundaries for hands-free turns, without extra dependencies."""

from __future__ import annotations

import asyncio
import logging
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
        observed = interval_peak = 0.0
        first_chunk = True
        started = False
        log = logging.getLogger("AUDIO")
        log.info("Escucha local: umbral RMS %.2f%%, pausa %.2f s", self.threshold / 32768 * 100, self.silence)
        async with aclosing(self.microphone.chunks(stop)) as source:
            async for pcm in source:
                samples = array("h", pcm)
                duration = len(samples) / self.sample_rate
                if not samples:
                    continue
                rms = math.sqrt(sum(value * value for value in samples) / len(samples))
                if first_chunk:
                    log.info("Micrófono entregando audio; primer bloque RMS %.2f%%", rms / 32768 * 100)
                    first_chunk = False
                voiced = rms >= self.threshold
                if not started:
                    pre_roll.append((pcm, duration, voiced))
                    buffered += duration
                    loud += duration if voiced else 0.0
                    while pre_roll and buffered - pre_roll[0][1] > 0.3:
                        _, old_duration, old_voiced = pre_roll.popleft()
                        buffered -= old_duration
                        loud -= old_duration if old_voiced else 0.0
                    observed += duration
                    interval_peak = max(interval_peak, rms)
                    if loud + 1e-9 < self.minimum:
                        if observed >= 5:
                            log.info("Esperando voz: RMS máximo %.2f%%; umbral %.2f%%", interval_peak / 32768 * 100,
                                     self.threshold / 32768 * 100)
                            observed = interval_peak = 0.0
                        continue
                    started = True
                    log.info("Voz detectada; enviando intervención.")
                    for chunk, _, _ in pre_roll:
                        yield chunk
                    pre_roll.clear()
                else:
                    yield pcm
                elapsed += duration
                quiet = 0.0 if voiced else quiet + duration
                if quiet + 1e-9 >= self.silence or elapsed + 1e-9 >= self.maximum:
                    log.info("Fin de intervención: %s", "pausa" if quiet + 1e-9 >= self.silence else "límite de tiempo")
                    stop.set()
                    return
