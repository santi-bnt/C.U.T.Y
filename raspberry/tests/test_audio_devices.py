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
