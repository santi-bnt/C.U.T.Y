"""Audio device discovery and selection."""

from __future__ import annotations

from array import array
from math import sqrt
from typing import Any


class AudioDeviceError(RuntimeError):
    pass


def _sounddevice() -> Any:
    try:
        import sounddevice as sd
    except (ImportError, OSError) as exc:
        raise AudioDeviceError("sounddevice/PortAudio is unavailable. Install requirements and check audio drivers.") from exc
    return sd


def list_devices() -> list[dict[str, object]]:
    sd = _sounddevice()
    return [
        {"index": index, "name": item["name"], "inputs": item["max_input_channels"], "outputs": item["max_output_channels"]}
        for index, item in enumerate(sd.query_devices())
    ]


def resolve_device(selector: str | None, *, input_device: bool) -> tuple[int, str]:
    devices = list_devices()
    direction = "inputs" if input_device else "outputs"
    if selector is None:
        sd = _sounddevice()
        default = sd.default.device[0 if input_device else 1]
        if default is None or int(default) < 0:
            raise AudioDeviceError(f"No default {'microphone' if input_device else 'speaker'} is configured.")
        matches = [item for item in devices if item["index"] == int(default)]
    elif selector.isdigit():
        matches = [item for item in devices if item["index"] == int(selector)]
    else:
        matches = [item for item in devices if selector.casefold() in str(item["name"]).casefold()]
        if len(matches) > 1:
            raise AudioDeviceError(f"Audio device '{selector}' is ambiguous. Use its index from --list-audio-devices.")
    if not matches or not isinstance(matches[0][direction], int) or matches[0][direction] <= 0:
        raise AudioDeviceError(f"No usable {'microphone' if input_device else 'speaker'} matches '{selector or 'default'}'.")
    item = matches[0]
    return int(item["index"]), str(item["name"])


def select_working_device(selector: str | None, *, input_device: bool, sample_rate: int = 24000) -> tuple[int, str]:
    """Open the stream briefly; Windows MME defaults can pass settings checks but fail to open."""
    index, name = resolve_device(selector, input_device=input_device)
    try:
        _probe(index, input_device=input_device, sample_rate=sample_rate)
        return index, name
    except AudioDeviceError as first_error:
        if selector is not None:
            raise first_error
        # Try another host API for the same physical device, not an unrelated mic.
        prefix = name.casefold()[:20]
        direction = "inputs" if input_device else "outputs"
        for item in list_devices():
            if item["index"] == index or not str(item["name"]).casefold().startswith(prefix) or item[direction] == 0:
                continue
            try:
                _probe(int(item["index"]), input_device=input_device, sample_rate=sample_rate)
                return int(item["index"]), str(item["name"])
            except AudioDeviceError:
                continue
        raise AudioDeviceError(f"{first_error} Use --list-audio-devices and set CUTY_AUDIO_{'INPUT' if input_device else 'OUTPUT'}_DEVICE.") from first_error


def _probe(index: int, *, input_device: bool, sample_rate: int) -> None:
    sd = _sounddevice()
    stream_class = sd.RawInputStream if input_device else sd.RawOutputStream
    try:
        with stream_class(samplerate=sample_rate, channels=1, dtype="int16", device=index, blocksize=sample_rate // 50):
            pass
    except (sd.PortAudioError, OSError) as exc:
        kind = "microphone" if input_device else "speaker"
        raise AudioDeviceError(f"Cannot open {kind} device {index}: {exc}") from exc


def format_devices() -> str:
    rows = ["Index  In  Out  Name"]
    for item in list_devices():
        rows.append(f"{item['index']:>5}  {item['inputs']:>2}  {item['outputs']:>3}  {item['name']}")
    return "\n".join(rows)


def test_microphone_level(selector: str | None, *, seconds: int = 3) -> tuple[str, float, float]:
    """Measure a short local recording without saving audio or contacting an AI service."""
    sample_rate = 16_000
    index, name = select_working_device(selector, input_device=True, sample_rate=sample_rate)
    sd = _sounddevice()
    frames = sample_rate // 10
    peak = 0
    power = 0
    sample_count = 0
    try:
        with sd.RawInputStream(samplerate=sample_rate, channels=1, dtype="int16", device=index, blocksize=frames) as stream:
            for _ in range(seconds * 10):
                data, overflowed = stream.read(frames)
                if overflowed:
                    raise AudioDeviceError("Microphone overflowed during the level test.")
                samples = array("h")
                samples.frombytes(bytes(data))
                peak = max(peak, max((abs(sample) for sample in samples), default=0))
                power += sum(sample * sample for sample in samples)
                sample_count += len(samples)
    except (sd.PortAudioError, OSError) as exc:
        raise AudioDeviceError(f"Cannot test microphone device {index}: {exc}") from exc
    rms = sqrt(power / sample_count) if sample_count else 0.0
    return name, peak / 32768 * 100, rms / 32768 * 100
