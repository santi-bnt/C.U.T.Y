import threading
import time

import pytest

from cuty.hardware.calibration_profile import AxisCalibration, RobotCalibration
from cuty.hardware.motion_actions import MotionAction
from cuty.hardware.robot_commands import parse_response
from cuty.hardware.robot_motion import RobotMotionExecutor


def profile():
    return RobotCalibration(tuple(AxisCalibration(
        axis=axis, pin=pin, min_us=1200, center_us=1500, max_us=1800,
        reverse=False, max_velocity_per_s=0.2, max_acceleration_per_s2=0.4,
        mechanical_calibration_confirmed=True, joint_mapping_confirmed=True,
    ) for axis, pin in (("HEAD_PAN", "PB6/J7"), ("LEFT_ARM", "PB7/J8"),
                        ("RIGHT_ARM", "PB8/J9"))))


class FakeBridge:
    def __init__(self, *_args):
        self.sequence = 0
        self.state = "DISARMED"
        self.commands = []
        self.closed = False
        self.events = []

    def exchange(self, wire, timeout=1):
        self.commands.append(wire.decode("ascii").strip())
        self.sequence += 1
        verb = wire.decode("ascii").strip().split(",")
        if verb[1] == "ARM":
            self.state = "READY"
        elif verb[1] == "START":
            self.state = "ACTIVE"
        elif verb[1] == "DISARM":
            self.state = "DISARMED"
        if verb[1] == "HB":
            self.events.append(parse_response(
                "V2,TELEM,9876,DISARMED,3,1,-125,200,0,OK"
            ))
        return f"V2,ACK,{self.sequence},OK,{self.state}\n"

    def drain_events(self):
        events, self.events = tuple(self.events), []
        return events

    def close(self):
        self.closed = True


def test_gesture_uses_v2_targets_and_stop_disarms():
    bridge = FakeBridge()
    executor = RobotMotionExecutor("/dev/test", profile(), bridge_factory=lambda *_: bridge,
                                   sleep=lambda _seconds: None)
    assert executor.enable()
    result = executor.execute(MotionAction.WAVE_BOTH)
    assert result["accepted"] is True
    assert "V2,TARGET,LEFT_ARM,200" in bridge.commands
    assert "V2,TARGET,RIGHT_ARM,200" in bridge.commands
    executor.stop()
    assert "V2,DISARM" in bridge.commands
    assert not bridge.closed
    executor.disable()
    assert bridge.closed


def test_motion_requires_local_enable_and_rejects_unexpected_state():
    executor = RobotMotionExecutor("/dev/test", profile(), bridge_factory=lambda *_: FakeBridge())
    with pytest.raises(RuntimeError):
        executor.execute(MotionAction.HEAD_LEFT)


def test_status_snapshot_reports_commanded_telemetry_without_claiming_measurement():
    bridge = FakeBridge()
    executor = RobotMotionExecutor("/dev/test", profile(), bridge_factory=lambda *_: bridge)
    executor.enable()
    snapshot = executor.status_snapshot()
    assert snapshot["connection"] == "connected"
    assert snapshot["safety_state"] == "DISARMED"
    assert snapshot["motion_authorized"] is True
    assert snapshot["position_kind"] == "commanded"
    assert snapshot["measured_positions_available"] is False
    assert snapshot["commanded_milli_units"] == {
        "HEAD_PAN": -125, "LEFT_ARM": 200, "RIGHT_ARM": 0,
    }
    executor.disable()
    assert "V2,DISARM" in bridge.commands


def test_reconnect_never_restores_motion_authorization_or_restarts_motion():
    bridges = []
    attempts = 0

    def bridge_factory(*_args):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OSError("UART disconnected")
        bridge = FakeBridge()
        bridge.state = "ACTIVE"
        bridges.append(bridge)
        return bridge

    executor = RobotMotionExecutor("/dev/test", profile(), bridge_factory=bridge_factory)
    assert executor.enable() is False
    deadline = time.monotonic() + 3
    while not executor.connected and time.monotonic() < deadline:
        time.sleep(0.02)
    try:
        assert executor.connected is True
        assert executor.enabled is False
        assert executor.status_snapshot()["motion_authorized"] is False
        with pytest.raises(RuntimeError, match="desautorizado"):
            executor.execute(MotionAction.HEAD_LEFT)
        assert executor.connected is True
        assert all(
            command.split(",")[1] not in {"ARM", "START"}
            for command in bridges[0].commands
        )
        assert "V2,DISARM" in bridges[0].commands
    finally:
        executor.disable()


def test_stop_cancels_a_gesture_before_any_later_target_is_sent():
    entered_step = threading.Event()
    release_step = threading.Event()

    def paused_sleep(_seconds):
        entered_step.set()
        release_step.wait(1)

    bridge = FakeBridge()
    executor = RobotMotionExecutor(
        "/dev/test", profile(), bridge_factory=lambda *_: bridge, sleep=paused_sleep,
    )
    assert executor.enable()
    result = []
    action = threading.Thread(target=lambda: result.append(executor.execute(MotionAction.WAVE_BOTH)))
    action.start()
    assert entered_step.wait(1)
    stopper = threading.Thread(target=executor.stop)
    stopper.start()
    assert executor._motion_cancel.wait(1)
    release_step.set()
    action.join(1)
    stopper.join(1)
    assert not action.is_alive() and not stopper.is_alive()
    disarm = max(index for index, line in enumerate(bridge.commands) if line == "V2,DISARM")
    assert all(line.split(",")[1] not in {"ARM", "START", "TARGET"}
               for line in bridge.commands[disarm + 1:])
    assert result == [{"accepted": False, "action": "wave_both", "mode": "robot",
                       "reason": "cancelled by stop"}]
    executor.disable()
