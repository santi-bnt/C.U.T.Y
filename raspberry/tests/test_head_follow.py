"""Pure simulated head-follow tests: no OpenCV, camera, serial port, or servos."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from cuty.vision.head_follow import (
    FaceFollowConfig,
    FaceFollowController,
    FollowConfigurationError,
    SimulatedHeadAdapter,
)
from cuty.brain.states import State, StateMachine


def config(**kwargs):
    return replace(FaceFollowConfig(enabled=True), **kwargs)


def target(x=0.5, y=0.5, timestamp=0.0):
    return SimpleNamespace(x=x, y=y, timestamp=timestamp)


def primed(config_override=None, *, adapter=None):
    c = FaceFollowController(config_override or config(), adapter=adapter)
    c.update(target(timestamp=0.0), now=0.0)
    return c


@pytest.mark.parametrize(("x", "expected_sign"), [(0.1, -1), (0.9, 1)])
def test_pan_error_sign_for_faces_left_and_right(x, expected_sign):
    c = primed(config(detection_alpha=1.0, kp=2.0, kd=0.0, max_acceleration=100.0))
    state = c.update(target(x=x, timestamp=0.1), now=0.1)
    assert state.x_error * expected_sign > 0
    assert state.pid_output * expected_sign > 0


@pytest.mark.parametrize(("y", "expected_sign"), [(0.1, -1), (0.9, 1)])
def test_vertical_error_is_reported_but_never_drives_unconfirmed_tilt(y, expected_sign):
    c = primed(config(detection_alpha=1.0, kp=0.0, kd=0.0))
    state = c.update(target(y=y, timestamp=0.1), now=0.1)
    assert state.y_error * expected_sign > 0
    assert state.pid_output == 0


def test_pid_saturation_and_conditional_anti_windup():
    c = primed(config(detection_alpha=1.0, kp=100.0, ki=2.0, kd=0.0,
                      max_velocity=0.1, max_acceleration=100.0))
    for i in range(1, 20):
        state = c.update(target(x=1.0, timestamp=i * 0.05), now=i * 0.05)
    assert state.pid_output == pytest.approx(0.1)
    assert c._pid.integral == 0.0
    reverse = c.update(target(x=0.0, timestamp=1.0), now=1.0)
    assert reverse.pid_output < 0


def test_jitter_is_filtered_and_outputs_remain_finite_and_bounded():
    c = primed(config(detection_alpha=0.2, derivative_alpha=0.15, kp=1.0,
                      ki=0.0, kd=0.2, max_acceleration=20.0))
    for i, (dt, x) in enumerate([(0.018, .54), (.09, .46), (.022, .53), (.07, .47)], 1):
        now = c._last_time + dt
        state = c.update(target(x=x, timestamp=now), now=now)
        assert state.pid_output == state.pid_output  # not NaN
        assert abs(state.velocity) <= c.config.max_velocity
        assert abs(state.simulated_position) <= 1.0


def test_invalid_dt_stops_output_without_dividing_by_zero():
    adapter = SimulatedHeadAdapter()
    c = primed(config(detection_alpha=1.0, kp=1.0, kd=1.0), adapter=adapter)
    state = c.update(target(x=.9, timestamp=0.0), now=0.0)
    assert state.reason == "invalid dt; output stopped"
    assert state.velocity == 0 and adapter.velocity == 0


def test_invalid_detection_and_face_timeout_hold_position_and_stop_once():
    adapter = SimulatedHeadAdapter()
    c = primed(config(detection_alpha=1.0, kp=1.0, kd=0.0, max_acceleration=100.0), adapter=adapter)
    c.update(target(x=.9, timestamp=.1), now=.1)
    moving_position = c.status.simulated_position
    assert moving_position > 0
    state = c.update(target(x=.9, timestamp=.1), now=.7)
    assert not state.tracking and state.velocity == 0
    assert state.simulated_position == moving_position
    commands = adapter.commands
    c.update(None, now=.8)
    assert adapter.commands == commands


def test_velocity_acceleration_and_simulated_travel_limits():
    c = primed(config(detection_alpha=1.0, kp=100.0, kd=0.0, max_velocity=.2,
                      max_acceleration=.5, min_position=-.03, max_position=.03))
    state = c.update(target(x=1.0, timestamp=.1), now=.1)
    assert state.velocity == pytest.approx(.05)  # acceleration * dt
    for i in range(2, 30):
        state = c.update(target(x=1.0, timestamp=i * .1), now=i * .1)
    assert state.simulated_position == pytest.approx(.03)
    assert state.velocity == 0


def test_manual_disable_is_immediate_and_cannot_be_overridden_by_detections():
    adapter = SimulatedHeadAdapter()
    c = primed(config(detection_alpha=1.0, kp=2.0), adapter=adapter)
    c.update(target(x=.9, timestamp=.1), now=.1)
    c.set_enabled(False)
    commands = adapter.commands
    assert adapter.velocity == 0
    assert c.update(target(x=0.0, timestamp=.2), now=.2).reason == "manual stop"
    assert adapter.commands == commands


def test_physical_activation_is_rejected_without_verified_adapter():
    with pytest.raises(FollowConfigurationError, match="Physical head following is blocked"):
        FaceFollowConfig(enabled=True, dry_run=False)


def test_default_is_disabled_and_dry_run():
    c = FaceFollowConfig()
    assert not c.enabled and c.dry_run and c.ki == 0


def test_follow_controller_does_not_override_voice_or_music_robot_states():
    states = StateMachine()
    states.set(State.MUSIC_PLAYING)
    c = primed(config(detection_alpha=1.0, kp=1.0))
    c.update(target(x=.9, timestamp=.1), now=.1)
    assert states.current is State.MUSIC_PLAYING
    states.set(State.LISTENING)
    c.update(target(x=.8, timestamp=.2), now=.2)
    assert states.current is State.LISTENING
