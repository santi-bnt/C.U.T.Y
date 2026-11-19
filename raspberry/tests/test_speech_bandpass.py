import math
import struct

import pytest

from cuty.audio.speech_bandpass import SpeechBandpass, design_bandpass


def gain(coefficients, rate, hz):
    response = sum(c * complex(math.cos(-2 * math.pi * hz * i / rate),
                               math.sin(-2 * math.pi * hz * i / rate))
                   for i, c in enumerate(coefficients))
    return abs(response)


@pytest.mark.parametrize("rate", [16000, 24000])
def test_design_symmetry_dc_zero_band_gain_stopband_and_delay(rate):
    h = design_bandpass(rate)
    assert len(h) == 511 and h == pytest.approx(h[::-1], abs=1e-14)
    assert gain(h, rate, 0) < 0.003
    assert gain(h, rate, 1000) == pytest.approx(1, abs=0.003)
    assert gain(h, rate, 500) > 0.98
    assert gain(h, rate, 100) < 0.08
    assert gain(h, rate, 6000 if rate == 16000 else 9000) < 0.01
    assert (len(h) - 1) / 2 / rate == pytest.approx(0.0159375 if rate == 16000 else 0.010625)
    phase = lambda hz: math.atan2(
        sum(-c * math.sin(2 * math.pi * hz * i / rate) for i, c in enumerate(h)),
        sum(c * math.cos(2 * math.pi * hz * i / rate) for i, c in enumerate(h)),
    )
    delta = phase(1010) - phase(1000)
    wrapped = math.atan2(math.sin(delta), math.cos(delta))
    expected = -2 * math.pi * 10 * 255 / rate
    assert wrapped == pytest.approx(math.atan2(math.sin(expected), math.cos(expected)), abs=1e-10)


def test_impulse_step_and_constant_are_finite_and_have_expected_response():
    fir = SpeechBandpass(16000, enabled=True)
    impulse = struct.pack("<h", 32767) + bytes(2 * 510)
    output = fir.process(impulse)
    values = struct.unpack("<511h", output)
    assert len(values) == 511 and all(math.isfinite(v) for v in values)
    assert values == pytest.approx([round(c * 32767) for c in fir.coefficients], abs=1)
    fir.reset()
    step = struct.pack("<h", 12000) * 2000
    step_out = struct.unpack("<2000h", fir.process(step))
    assert max(abs(v) for v in step_out[-100:]) < 100  # DC is rejected.


def test_passband_tone_survives_and_out_of_band_tone_is_attenuated():
    rate = 16000
    samples = [round(5000 * math.sin(2 * math.pi * 1000 * n / rate)
                     + 5000 * math.sin(2 * math.pi * 6000 * n / rate)) for n in range(4096)]
    packed = struct.pack("<" + "h" * len(samples), *samples)
    filtered = SpeechBandpass(rate, enabled=True).process(packed)
    got = struct.unpack("<" + "h" * len(samples), filtered)[1024:]
    # RMS of the mixed signal remains substantial; finite/clamped PCM is preserved.
    rms = math.sqrt(sum(v * v for v in got) / len(got))
    assert 2500 < rms < 5000
    assert len(filtered) == len(packed) and min(got) >= -32768 and max(got) <= 32767

    def amplitude(values, hz):
        re = sum(v * math.cos(2 * math.pi * hz * n / rate) for n, v in enumerate(values))
        im = sum(v * math.sin(2 * math.pi * hz * n / rate) for n, v in enumerate(values))
        return 2 * math.hypot(re, im) / len(values)

    source = samples[1024:]
    assert amplitude(got, 1000) / amplitude(source, 1000) > 0.98
    assert amplitude(got, 6000) / amplitude(source, 6000) < 0.01


def test_block_continuity_bypass_stereo_and_pcm_errors():
    import random
    rng = random.Random(3)
    pcm = struct.pack("<" + "h" * 1024, *(rng.randrange(-12000, 12000) for _ in range(1024)))
    whole = SpeechBandpass(16000, enabled=True).process(pcm)
    chunked_fir = SpeechBandpass(16000, enabled=True)
    chunked = b"".join(chunked_fir.process(pcm[i:i + 640]) for i in range(0, len(pcm), 640))
    assert chunked == whole
    assert SpeechBandpass(16000).process(pcm) is pcm
    stereo = SpeechBandpass(16000, enabled=True, channels=2)
    assert len(stereo.process(pcm)) == len(pcm)
    with pytest.raises(ValueError, match="incomplete"):
        stereo.process(b"\0\0\0")
    clipper = SpeechBandpass(16000, enabled=True, coefficients=(2.0,))
    assert struct.unpack("<h", clipper.process(struct.pack("<h", 32767)))[0] == 32767
    with pytest.raises(ValueError, match="odd-length"):
        SpeechBandpass(16000, coefficients=(1.0, 0.5))
    with pytest.raises(ValueError, match="Nyquist"):
        SpeechBandpass(8000, low_hz=150, high_hz=4000)


def test_env_disabled_by_default_and_validates_rate(monkeypatch):
    monkeypatch.delenv("CUTY_SPEECH_FIR_ENABLED", raising=False)
    assert not SpeechBandpass.from_env(16000).enabled
    monkeypatch.setenv("CUTY_SPEECH_FIR_ENABLED", "1")
    with pytest.raises(ValueError, match="Nyquist"):
        SpeechBandpass.from_env(8000)
