"""ALSA rate negotiation and streaming conversion without audio hardware."""

import asyncio
import math
from array import array

import pytest

from cuty.audio import devices, speaker
from cuty.audio.speaker import OutputPCM, SoundDeviceSpeaker


class Stream:
    def __init__(self):
        self.audio = bytearray()
        self.started = self.stopped = self.closed = False

    def start(self):
        self.started = True

    def write(self, pcm):
        self.audio.extend(pcm)

    def stop(self):
        self.stopped = True

    def close(self):
        self.closed = True


def test_explicit_alsa_device_uses_supported_stereo_rate_even_during_startup_probe(monkeypatch):
    streams, settings = [], []

    class SD:
        PortAudioError = RuntimeError

        def query_devices(self, *args):
            info = {"name": "seeed2micvoicec", "max_input_channels": 2,
                    "max_output_channels": 2, "default_samplerate": 48000.0}
            return info if args else [info]

        def check_output_settings(self, **kwargs):
            settings.append((kwargs["samplerate"], kwargs["channels"]))
            if (kwargs["samplerate"], kwargs["channels"]) != (16000, 2):
                raise self.PortAudioError("Invalid sample rate or channel count")

        def RawOutputStream(self, **kwargs):
            assert kwargs["samplerate"] == 16000 and kwargs["channels"] == 2
            stream = Stream()
            streams.append(stream)
            return stream

    monkeypatch.setattr(devices, "_sounddevice", lambda: SD())
    assert devices.select_working_device("0", input_device=False) == (0, "seeed2micvoicec")
    assert settings == [(24000, 1), (24000, 2), (16000, 1), (16000, 2)]
    assert streams[0].started and streams[0].stopped and streams[0].closed


@pytest.mark.parametrize("rate", [16000, 44100, 48000])
def test_resampling_preserves_duration_pitch_and_chunk_continuity(rate):
    pcm = array("h", (round(8000 * math.sin(2 * math.pi * 440 * i / 24000))
                      for i in range(24000))).tobytes()
    whole = OutputPCM(rate, 1)
    expected = whole.convert(pcm) + whole.flush()
    fragmented = OutputPCM(rate, 1)
    result = b"".join(fragmented.convert(pcm[i:i + 386]) for i in range(0, len(pcm), 386))
    result += fragmented.flush()
    assert result == expected
    samples = array("h", result)
    assert len(samples) == rate  # One second, not sped up or slowed down.
    crossings = sum(a <= 0 < b for a, b in zip(samples, samples[1:]))
    assert abs(crossings - 440) <= 1


def test_native_mono_is_unchanged_and_stereo_duplicates_both_channels():
    pcm = array("h", [0, 32767, -32768, 100]).tobytes()
    assert OutputPCM(24000, 1).convert(pcm) == pcm
    assert list(array("h", OutputPCM(24000, 2).convert(pcm))) == [0, 0, 32767, 32767, -32768, -32768, 100, 100]


def test_playback_flushes_converter_before_closing_stream(monkeypatch):
    stream = Stream()
    monkeypatch.setattr(speaker, "open_output_stream", lambda device: (stream, 16000, 2))
    monkeypatch.setattr(speaker, "_sounddevice", lambda: type("SD", (), {"PortAudioError": OSError}))

    async def run():
        output = SoundDeviceSpeaker(1)
        await output.open()
        for _ in range(50):
            await output.write(array("h", [1000] * 480).tobytes())
        await output.close()
        await output.close()

    asyncio.run(run())
    assert len(stream.audio) == 16000 * 2 * 2  # seconds * samples * stereo * bytes
    assert stream.stopped and stream.closed


def test_failed_start_closes_allocated_output_stream(monkeypatch):
    opened = []

    class SD:
        PortAudioError = RuntimeError

        def query_devices(self, *args):
            return {"default_samplerate": 16000, "max_output_channels": 1}

        def check_output_settings(self, **kwargs):
            pass

        def RawOutputStream(self, **kwargs):
            stream = Stream()

            def fail():
                raise RuntimeError("Device busy")

            stream.start = fail
            opened.append(stream)
            return stream

    monkeypatch.setattr(devices, "_sounddevice", lambda: SD())
    with pytest.raises(devices.AudioDeviceError, match="Device busy"):
        devices.open_output_stream(1)
    assert opened and all(stream.closed for stream in opened)
