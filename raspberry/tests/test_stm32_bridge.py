import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cuty.hardware.robot_commands import command, parse_response, parse_telemetry, target
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


def test_telemetry_parser_distinguishes_commanded_position_and_validates_bounds():
    sample = parse_telemetry(parse_response(
        "V2,TELEM,1234,ACTIVE,2,1,-150,250,0,OK"
    ))
    assert sample.commanded_milli_units == {
        "HEAD_PAN": -150, "LEFT_ARM": 250, "RIGHT_ARM": 0,
    }
    with pytest.raises(ValueError):
        parse_telemetry(parse_response(
            "V2,TELEM,1234,ACTIVE,2,1,-150,1001,0,OK"
        ))


def test_bridge_bounds_unconsumed_periodic_telemetry(tmp_path, monkeypatch):
    monkeypatch.setattr("cuty.hardware.stm32_bridge.Path", lambda _p: tmp_path)
    fake = FakeSerial()
    fake.lines = [
        *(f"V2,TELEM,{index},DISARMED,0,0,0,0,0,OK\n".encode() for index in range(100)),
        b"V2,ACK,1,OK,DISARMED\n",
    ]
    bridge = STM32Bridge("/dev/ttyS0", serial_factory=lambda *a, **k: fake)
    bridge.exchange(command("V2,HB"))
    assert len(bridge.events) == 64
    events = bridge.drain_events()
    assert len(events) == 64
    assert not bridge.events
    bridge.close()
