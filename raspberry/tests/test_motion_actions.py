import pytest

from cuty.hardware.motion_actions import (
    MotionAction,
    MotionActionGate,
    MotionRequest,
    parse_motion_request,
)


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
        gate.enable_physical(link_valid=True, calibration_complete=False)
    with pytest.raises(RuntimeError):
        gate.enable_physical(link_valid=False, calibration_complete=True)
