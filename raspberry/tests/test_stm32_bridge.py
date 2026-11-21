import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cuty.hardware.robot_commands import command, target
from cuty.hardware.stm32_bridge import STM32Bridge


def test_v2_serialization_and_validation():
    assert command("V2,HB") == b"V2,HB\n"
    assert target("HEAD_PAN", 350) == b"V2,TARGET,HEAD_PAN,350\n"
    with pytest.raises(ValueError):
        command("SET_HEAD,15")
    with pytest.raises(ValueError):
        target("J10", 0)


class FakeSerial:
    def __init__(self, *_args, **_kwargs):
        self.writes = []
        self.closed = False
        self.lines = [b"V2,ACK,1,OK,DISARMED\n", b"V2,ACK,2,OK,DISARMED\n"]

    def write(self, data):
        self.writes.append(data)
        return len(data)

    def flush(self):
        pass

    def readline(self):
        return self.lines.pop(0) if self.lines else b""

    def close(self):
        self.closed = True


def test_bridge_reply_and_close(tmp_path, monkeypatch):
    monkeypatch.setattr("cuty.hardware.stm32_bridge.Path", lambda _p: tmp_path)
    fake = FakeSerial()
    bridge = STM32Bridge("/dev/ttyS0", serial_factory=lambda *a, **k: fake)
    assert bridge.exchange(command("V2,HB")) == "V2,ACK,1,OK,DISARMED"
    assert fake.writes == [b"V2,HB\n"]
    bridge.close()
    assert fake.closed
    assert fake.writes[-1] == b"V2,DISARM\n"


def test_bridge_timeout_and_disconnect(tmp_path, monkeypatch):
    monkeypatch.setattr("cuty.hardware.stm32_bridge.Path", lambda _p: tmp_path)
    fake = FakeSerial()
    fake.lines = []
    bridge = STM32Bridge("/dev/ttyS0", serial_factory=lambda *a, **k: fake)
    with pytest.raises(ConnectionError, match="timeout"):
        bridge.exchange(command("V2,HB"), timeout=0)
    bridge.close()
