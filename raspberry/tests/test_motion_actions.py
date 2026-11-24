import pytest

from cuty.hardware.motion_actions import (
    MotionAction,
    MotionActionGate,
    MotionRequest,
    parse_motion_request,
)
from cuty.hardware.calibration_profile import AxisCalibration, RobotCalibration


@pytest.mark.parametrize(("spoken", "action"), [
    ("Cuty, saluda", MotionAction.WAVE_RIGHT),
    ("levanta el brazo izquierdo", MotionAction.ARM_LEFT),
    ("Mira a la derecha", MotionAction.HEAD_RIGHT),
    ("regresa al centro", MotionAction.HEAD_CENTER),
    ("por favor detente ahora", MotionAction.STOP),
])
def test_allowlisted_voice_requests(spoken, action):
    assert parse_motion_request(spoken) == MotionRequest(action)


@pytest.mark.parametrize("spoken", ["mueve un poco", "saluda y gira", "", "a" * 241])
def test_ambiguous_or_invalid_voice_requests_are_rejected(spoken):
    with pytest.raises(ValueError):
        parse_motion_request(spoken)


def test_simulation_is_default_and_stop_has_priority():
    gate = MotionActionGate()
    result = gate.submit(parse_motion_request("saluda"))
    assert result["accepted"] is False
    assert result["mode"] == "simulation"
    assert gate.submit(parse_motion_request("saluda, detente"))["action"] == "stop"


def test_physical_enable_requires_link_and_complete_calibration():
    gate = MotionActionGate(executor=object())
    with pytest.raises(RuntimeError):
        gate.enable_physical(calibration=None)
    with pytest.raises(RuntimeError):
        gate.enable_physical(calibration=RobotCalibration(()))


def test_calibration_profile_requires_all_confirmed_mapped_axes():
    axes = tuple(AxisCalibration(
        axis=axis, pin=pin, min_us=1200, center_us=1500, max_us=1800,
        reverse=False, max_velocity_per_s=0.2, max_acceleration_per_s2=0.4,
        mechanical_calibration_confirmed=True, joint_mapping_confirmed=True,
    ) for axis, pin in (("HEAD_PAN", "PB6/J7"), ("LEFT_ARM", "PB7/J8"),
                        ("RIGHT_ARM", "PB8/J9")))
    RobotCalibration(axes).validate_complete()
    with pytest.raises(ValueError):
        RobotCalibration(axes[:2]).validate_complete()
    with pytest.raises(ValueError):
        AxisCalibration(**{**axes[0].__dict__, "pin": "PB9/J10"}).validate()
