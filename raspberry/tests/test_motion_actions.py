import pytest

from cuty.hardware.motion_actions import (
    MotionAction,
    MotionActionGate,
    MotionRequest,
    OperationMode,
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
    assert result["accepted"] is True
    assert result["mode"] == "simulation"
    assert result["simulated"] is True
    assert gate.submit(parse_motion_request("mira a la izquierda"))["commanded_milli_units"]["HEAD_PAN"] == -150
    assert gate.status_snapshot()["position_kind"] == "commanded"
    assert gate.status_snapshot()["measured_positions_available"] is False
    assert gate.status_snapshot()["motion_authorized"] is False
    assert gate.submit(parse_motion_request("saluda, detente"))["action"] == "stop"
    assert gate.status_snapshot()["controller_active"] is False


def test_simulated_gesture_interpolates_and_can_be_stopped(monkeypatch):
    from cuty.hardware import motion_actions

    now = [10.0]
    monkeypatch.setattr(motion_actions.time, "monotonic", lambda: now[0])
    gate = MotionActionGate()
    gate.submit(MotionRequest(MotionAction.WAVE_LEFT))
    assert gate.status_snapshot()["commanded_milli_units"]["LEFT_ARM"] == 0
    now[0] += 0.125
    middle = gate.status_snapshot()
    assert middle["commanded_milli_units"]["LEFT_ARM"] == 100
    assert middle["controller_active"] is True
    gate.submit(MotionRequest(MotionAction.STOP))
    stopped = gate.status_snapshot()
    assert stopped["commanded_milli_units"]["LEFT_ARM"] == 100
    assert stopped["controller_active"] is False


def test_physical_enable_requires_link_and_complete_calibration():
    gate = MotionActionGate(executor=object())
    with pytest.raises(RuntimeError):
        gate.enable_physical(calibration=None)
    with pytest.raises(RuntimeError):
        gate.enable_physical(calibration=RobotCalibration(()))


def _confirmed_profile():
    axes = tuple(AxisCalibration(
        axis=axis, pin=pin, min_us=1200, center_us=1500, max_us=1800,
        reverse=False, max_velocity_per_s=0.2, max_acceleration_per_s2=0.4,
        mechanical_calibration_confirmed=True, joint_mapping_confirmed=True,
    ) for axis, pin in (("HEAD_PAN", "PB6/J7"), ("LEFT_ARM", "PB7/J8"),
                        ("RIGHT_ARM", "PB8/J9")))
    return RobotCalibration(axes)


def test_test_mode_limits_actions_to_one_calibrated_axis():
    class Executor:
        def __init__(self):
            self.actions = []
            self.disabled = False

        def enable(self):
            return True

        def execute(self, action):
            self.actions.append(action)
            return {"accepted": True, "action": action.value}

        def stop(self):
            pass

        def disable(self):
            self.disabled = True

    executor = Executor()
    gate = MotionActionGate(executor)
    gate.enable_test(axis="LEFT_ARM", calibration=_confirmed_profile())
    assert gate.mode is OperationMode.TEST
    assert gate.submit(MotionRequest(MotionAction.WAVE_LEFT))["accepted"] is True
    rejected = gate.submit(MotionRequest(MotionAction.WAVE_BOTH))
    assert rejected["accepted"] is False
    assert rejected["mode"] == "test"
    assert executor.actions == [MotionAction.WAVE_LEFT]
    with pytest.raises(RuntimeError, match="Vuelve a SIMULATION"):
        gate.enable_physical(calibration=_confirmed_profile())
    gate.select_simulation()
    assert gate.mode is OperationMode.SIMULATION
    assert executor.disabled is True
    gate.enable_physical(calibration=_confirmed_profile())
    assert gate.mode is OperationMode.ROBOT


def test_test_mode_needs_a_valid_axis_and_calibration():
    gate = MotionActionGate(executor=object())
    with pytest.raises(RuntimeError, match="eje válido"):
        gate.enable_test(axis="J10", calibration=_confirmed_profile())
    with pytest.raises(RuntimeError, match="calibración completa"):
        gate.enable_test(axis="HEAD_PAN", calibration=RobotCalibration(()))


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
