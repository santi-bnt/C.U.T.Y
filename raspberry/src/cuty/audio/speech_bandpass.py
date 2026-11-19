"""Stateful windowed-sinc FIR for incoming microphone PCM16."""
from __future__ import annotations

import math
import os
import numpy as np

DEFAULT_LOW_HZ = 150.0
DEFAULT_HIGH_HZ = 4000.0
DEFAULT_TAPS = 511


def design_bandpass(sample_rate: int, low_hz: float = DEFAULT_LOW_HZ,
                    high_hz: float = DEFAULT_HIGH_HZ, taps: int = DEFAULT_TAPS) -> tuple[float, ...]:
    """Odd-length Hamming-windowed ideal bandpass, normalized at band center."""
    if sample_rate <= 0 or taps < 3 or taps % 2 == 0:
        raise ValueError("sample_rate must be positive and taps must be odd and >= 3")
    if not (math.isfinite(low_hz) and math.isfinite(high_hz)
            and 0 < low_hz < high_hz < sample_rate / 2):
        raise ValueError("FIR edges must satisfy 0 < low < high < Nyquist")
    middle = (taps - 1) / 2

    def lowpass(cutoff: float, n: int) -> float:
        normalized = cutoff / sample_rate
        if n == 0:
            return 2 * normalized
        return math.sin(2 * math.pi * normalized * n) / (math.pi * n)

    coeffs = []
    for i in range(taps):
        n = i - middle
        ideal = lowpass(high_hz, int(n)) - lowpass(low_hz, int(n))
        window = 0.54 - 0.46 * math.cos(2 * math.pi * i / (taps - 1))
        coeffs.append(ideal * window)
    center_hz = (low_hz + high_hz) / 2
    response = sum(c * complex(math.cos(-2 * math.pi * center_hz * i / sample_rate),
                               math.sin(-2 * math.pi * center_hz * i / sample_rate))
                   for i, c in enumerate(coeffs))
    gain = abs(response)
    if not math.isfinite(gain) or gain < 1e-12:
        raise ValueError("Could not normalize FIR coefficients")
    return tuple(c / gain for c in coeffs)


class SpeechBandpass:
    """PCM16 little-endian filter; one independent delay line per interleaved channel."""

    def __init__(self, sample_rate: int, *, enabled: bool = False, low_hz: float = DEFAULT_LOW_HZ,
                 high_hz: float = DEFAULT_HIGH_HZ, channels: int = 1,
                 coefficients: tuple[float, ...] | None = None) -> None:
        if channels not in (1, 2):
            raise ValueError("channels must be 1 or 2")
        self.sample_rate, self.channels = sample_rate, channels
        self.coefficients = tuple(coefficients) if coefficients is not None else design_bandpass(sample_rate, low_hz, high_hz)
        if not self.coefficients or len(self.coefficients) % 2 == 0 or not all(math.isfinite(c) for c in self.coefficients):
            raise ValueError("coefficients must be finite, non-empty, and odd-length")
        self.enabled = enabled
        self._history = np.zeros((max(0, len(self.coefficients) - 1), channels), dtype=np.float64)

    @classmethod
    def from_env(cls, sample_rate: int) -> "SpeechBandpass":
        def number(name: str, default: float) -> float:
            try:
                result = float(os.getenv(name, str(default)))
            except ValueError as exc:
                raise ValueError(f"{name} must be numeric") from exc
            if not math.isfinite(result):
                raise ValueError(f"{name} must be finite")
            return result

        enabled = os.getenv("CUTY_SPEECH_FIR_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
        return cls(sample_rate, enabled=enabled,
                   low_hz=number("CUTY_SPEECH_FIR_LOW_HZ", DEFAULT_LOW_HZ),
                   high_hz=number("CUTY_SPEECH_FIR_HIGH_HZ", DEFAULT_HIGH_HZ))

    @property
    def group_delay_seconds(self) -> float:
        return ((len(self.coefficients) - 1) / 2) / self.sample_rate

    def reset(self) -> None:
        self._history.fill(0.0)

    def process(self, pcm16: bytes) -> bytes:
        frame_bytes = self.channels * 2
        if len(pcm16) % frame_bytes:
            raise ValueError("PCM16 block has incomplete sample frame")
        if not self.enabled or not pcm16:
            return pcm16
        samples = np.frombuffer(pcm16, dtype="<i2").reshape(-1, self.channels).astype(np.float64) / 32768.0
        joined = np.concatenate((self._history, samples), axis=0)
        filtered = np.empty_like(samples)
        for channel in range(self.channels):
            filtered[:, channel] = np.convolve(joined[:, channel], self.coefficients, mode="valid")
        if len(self._history):
            self._history[:] = joined[-len(self._history):]
        pcm = np.rint(filtered * 32768.0).clip(-32768, 32767).astype("<i2", copy=False)
        return pcm.tobytes()
