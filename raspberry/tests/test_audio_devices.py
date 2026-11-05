import pytest

from cuty.audio import devices


class FakeSD:
    class Default:
        device = (0, 2)

    default = Default()

    @staticmethod
    def query_devices():
        return [
            {"name": "Microphone Array (Realtek)", "max_input_channels": 2, "max_output_channels": 0},
            {"name": "Microphone Array (Realtek) DirectSound", "max_input_channels": 2, "max_output_channels": 0},
            {"name": "Speakers", "max_input_channels": 0, "max_output_channels": 2},
        ]


def test_list_and_select_fallback(monkeypatch):
    monkeypatch.setattr(devices, "_sounddevice", lambda: FakeSD())
    attempted = []

    def probe(index, *, input_device, sample_rate):
        attempted.append(index)
        if index == 0:
            raise devices.AudioDeviceError("default stream failed")

    monkeypatch.setattr(devices, "_probe", probe)
    assert devices.select_working_device(None, input_device=True)[0] == 1
    assert attempted == [0, 1]
    assert devices.resolve_device("Speakers", input_device=False)[0] == 2


def test_explicit_bad_device_does_not_fallback(monkeypatch):
    monkeypatch.setattr(devices, "_sounddevice", lambda: FakeSD())

    def fail(index, *, input_device, sample_rate):
        raise devices.AudioDeviceError("unavailable")

    monkeypatch.setattr(devices, "_probe", fail)
    with pytest.raises(devices.AudioDeviceError, match="unavailable"):
        devices.select_working_device("0", input_device=True)


def test_duplex_diagnostic_uses_one_stream_with_silent_output(monkeypatch):
    from array import array

    class SD(FakeSD):
        class PortAudioError(Exception):
            pass

        def RawStream(self, **kwargs):
            assert kwargs["device"] == (0, 2)
            assert kwargs["channels"] == (1, 1) and kwargs["samplerate"] == 16000
            callback = kwargs["callback"]

            class Stream:
                def __enter__(self):
                    for _ in range(150):
                        output = bytearray([255] * 640)
                        callback(array("h", [1000] * 320).tobytes(), output, 320, None, None)
                        assert output == bytes(640)

                def __exit__(self, *args):
                    pass

            return Stream()

        def sleep(self, milliseconds):
            assert milliseconds == 3000

    monkeypatch.setattr(devices, "_sounddevice", lambda: SD())
    mic, output, peak, rms = devices.test_duplex_level("0", "2")
    assert mic == "Microphone Array (Realtek)" and output == "Speakers"
    assert peak == pytest.approx(3.0517578125) and rms == pytest.approx(peak)


def test_duplex_diagnostic_rejects_stream_without_pcm(monkeypatch):
    class SD(FakeSD):
        class PortAudioError(Exception):
            pass

        def RawStream(self, **kwargs):
            class Stream:
                def __enter__(self):
                    pass

                def __exit__(self, *args):
                    pass

            return Stream()

        def sleep(self, milliseconds):
            pass

    monkeypatch.setattr(devices, "_sounddevice", lambda: SD())
    with pytest.raises(devices.AudioDeviceError, match="did not deliver enough PCM"):
        devices.test_duplex_level("0", "2")
