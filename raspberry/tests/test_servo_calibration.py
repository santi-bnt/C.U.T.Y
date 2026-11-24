"""Sesión de calibración con UART y reloj simulados, sin motores ni GPIO."""
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cuty.hardware import servo_calibration as module
from cuty.hardware.robot_commands import command


class FakeBridge:
    def __init__(self):
        self.serial = SimpleNamespace(reset_input_buffer=Mock())
        self._rx_buffer = bytearray()
        self.sequence = 0
        self.state = "DISARMED"
        self.sent = []
        self.reject_cal = False

    def exchange(self, wire, timeout=1):
        self.sent.append(wire)
        self.sequence += 1
        if wire == b"V2,DISARM\n" and self.state != "FAULT":
            self.state = "DISARMED"
        elif wire == b"V2,RESET\n":
            self.state = "DISARMED"
        elif wire == b"V2,ARM\n":
            self.state = "READY"
        if wire.startswith(b"V2,CAL") and self.reject_cal:
            return f"V2,NACK,{self.sequence},REJECTED,FAULT"
        return f"V2,ACK,{self.sequence},OK,{self.state}"

    def close(self):
        self.exchange(b"V2,DISARM\n")
        self.closed = True


def test_session_arms_once_and_uses_named_joint():
    bridge = FakeBridge()
    session = module.CalibrationSession(bridge, "LEFT_ARM")
    session.start()
    session.step(1)
    assert bridge.sent == [b"V2,DISARM\n", b"V2,HB\n", b"V2,ARM\n",
                           b"V2,CAL,LEFT_ARM,1500\n", b"V2,CAL,LEFT_ARM,1510\n"]
    assert session.pulse_us == 1510
    assert b"V2,START\n" not in bridge.sent


def test_fault_is_not_automatically_reset():
    bridge = FakeBridge()
    bridge.state = "FAULT"
    session = module.CalibrationSession(bridge, "HEAD_PAN")
    with pytest.raises(RuntimeError, match="FAULT"):
        session.start()
    assert bridge.sent == [b"V2,DISARM\n"]
    session = module.CalibrationSession(bridge, "HEAD_PAN")
    session.start(reset_fault=True)
    assert b"V2,RESET\n" in bridge.sent


def test_nack_never_advances_local_pulse():
    bridge = FakeBridge()
    session = module.CalibrationSession(bridge, "RIGHT_ARM")
    session.start()
    bridge.reject_cal = True
    with pytest.raises(RuntimeError):
        session.step(1)
    assert session.pulse_us == 1500


def test_stale_ack_fails_closed():
    bridge = FakeBridge()
    session = module.CalibrationSession(bridge, "LEFT_ARM")
    session.start()
    bridge.sequence -= 1
    with pytest.raises(RuntimeError, match="secuencia"):
        session.step(1)


def test_bounds_and_wire_validation():
    assert command("V2,CAL,HEAD_PAN,1500") == b"V2,CAL,HEAD_PAN,1500\n"
    for line in ["V2,CAL,J10,1500", "V2,CAL,HEAD_PAN,2001", "V2,CAL,HEAD_PAN,+500"]:
        with pytest.raises(ValueError):
            command(line)
    session = module.CalibrationSession(FakeBridge(), "LEFT_ARM")
    session.pulse_us = 2000
    with pytest.raises(ValueError):
        session.step(1)


def test_terminal_wait_still_sends_heartbeat_and_records_unconfirmed_points(monkeypatch):
    class Clock:
        now = 0
        def monotonic(self):
            return self.now
    clock = Clock()
    controls = iter([None, "+", "centro", "invertir", "q"])
    def read(timeout):
        clock.now += 0.15
        return next(controls)
    monkeypatch.setattr(module.time, "monotonic", clock.monotonic)
    bridge = FakeBridge()
    session = module.CalibrationSession(bridge, "LEFT_ARM")
    session.start()
    result = module.run_session(session, 10, read)
    assert bridge.sent.count(b"V2,HB\n") >= 4
    assert result["observed_points"] == {"center_us": 1510}
    assert result["mechanical_calibration_confirmed"] is False
    assert result["reverse"] is True


def test_unloaded_confirmation_is_required_before_opening_uart(monkeypatch):
    factory = Mock()
    monkeypatch.setattr(module, "STM32Bridge", factory)
    with pytest.raises(SystemExit) as error:
        module.main(["--port", "/dev/ttyAMA0", "--axis", "LEFT_ARM"])
    assert error.value.code == 2
    factory.assert_not_called()


def test_ctrl_c_requests_disarm_and_closes_before_leaving(tmp_path, monkeypatch):
    bridge = FakeBridge()
    monkeypatch.setattr(module, "STM32Bridge", lambda *_: bridge)
    monkeypatch.setattr(module, "os", SimpleNamespace(name="posix"))
    monkeypatch.setattr(module.sys, "stdin", SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr(module, "run_session", Mock(side_effect=KeyboardInterrupt))
    output = tmp_path / "not-saved.json"
    assert module.main(["--port", "/dev/ttyAMA0", "--axis", "LEFT_ARM",
                        "--confirm-unloaded", "--output", str(output)]) == 130
    assert bridge.sent[-1] == b"V2,DISARM\n" and bridge.closed
    assert not output.exists()
