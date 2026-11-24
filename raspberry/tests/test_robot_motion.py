import pytest

from cuty.hardware.calibration_profile import AxisCalibration, RobotCalibration
from cuty.hardware.motion_actions import MotionAction
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
        return f"V2,ACK,{self.sequence},OK,{self.state}\n".encode()

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
    assert "V2,DISARM\n" in bridge.commands
    assert bridge.closed


def test_motion_requires_local_enable_and_rejects_unexpected_state():
    executor = RobotMotionExecutor("/dev/test", profile(), bridge_factory=lambda *_: FakeBridge())
    with pytest.raises(RuntimeError):
        executor.execute(MotionAction.HEAD_LEFT)
