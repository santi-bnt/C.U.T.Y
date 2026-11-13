"""Safe, local face-to-head follow controller.

Only a normalized PAN simulation is implemented.  The repository has no
Raspberry/STM32 UART protocol, servo firmware, calibrated directions, or
verified physical travel/rate limits, so a hardware adapter is deliberately
not provided.
"""

from __future__ import annotations

import math
import os
import threading
import time
from dataclasses import dataclass
from typing import Protocol


class FollowConfigurationError(ValueError):
    """The requested tracking mode cannot safely be configured."""


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise FollowConfigurationError(f"{name} must be a number") from exc
    if not math.isfinite(value):
        raise FollowConfigurationError(f"{name} must be finite")
    return value


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    return default if raw is None else raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class FaceFollowConfig:
    enabled: bool = False
    dry_run: bool = True
    kp: float = 1.2
    ki: float = 0.0
    kd: float = 0.08
    detection_alpha: float = 0.35
    derivative_alpha: float = 0.25
    deadband: float = 0.035
    lost_timeout: float = 0.5
    max_dt: float = 0.25
    max_velocity: float = 0.8
    max_acceleration: float = 1.5
    min_position: float = -1.0
    max_position: float = 1.0

    def __post_init__(self) -> None:
        if self.enabled and not self.dry_run:
            raise FollowConfigurationError(
                "Physical head following is blocked: no verified UART/STM32 adapter, "
                "servo calibration, direction, or travel limits exist. Keep dry-run enabled."
            )
        if not 0 < self.detection_alpha <= 1:
            raise FollowConfigurationError("CUTY_FOLLOW_DETECTION_ALPHA must be in (0, 1]")
        if not 0 < self.derivative_alpha <= 1:
            raise FollowConfigurationError("CUTY_FOLLOW_DERIVATIVE_ALPHA must be in (0, 1]")
        if self.deadband < 0 or self.lost_timeout <= 0 or self.max_dt <= 0:
            raise FollowConfigurationError("deadband must be >= 0 and time limits must be > 0")
        if self.max_velocity <= 0 or self.max_acceleration <= 0:
            raise FollowConfigurationError("simulation velocity and acceleration limits must be > 0")
        if self.min_position >= self.max_position:
            raise FollowConfigurationError("simulation minimum position must be below maximum")
        if any(not math.isfinite(v) for v in (
            self.kp, self.ki, self.kd, self.deadband, self.lost_timeout,
            self.max_dt, self.max_velocity, self.max_acceleration,
            self.min_position, self.max_position,
        )):
            raise FollowConfigurationError("PID and simulation parameters must be finite")

    @classmethod
    def from_env(cls) -> "FaceFollowConfig":
        return cls(
            enabled=_bool_env("CUTY_FOLLOW_ENABLED", False),
            dry_run=_bool_env("CUTY_FOLLOW_DRY_RUN", True),
            kp=_float_env("CUTY_FOLLOW_KP", 1.2),
            ki=_float_env("CUTY_FOLLOW_KI", 0.0),
            kd=_float_env("CUTY_FOLLOW_KD", 0.08),
            detection_alpha=_float_env("CUTY_FOLLOW_DETECTION_ALPHA", 0.35),
            derivative_alpha=_float_env("CUTY_FOLLOW_DERIVATIVE_ALPHA", 0.25),
            deadband=_float_env("CUTY_FOLLOW_DEADBAND", 0.035),
            lost_timeout=_float_env("CUTY_FOLLOW_LOST_TIMEOUT", 0.5),
            max_dt=_float_env("CUTY_FOLLOW_MAX_DT", 0.25),
            max_velocity=_float_env("CUTY_FOLLOW_SIM_MAX_VELOCITY", 0.8),
            max_acceleration=_float_env("CUTY_FOLLOW_SIM_MAX_ACCELERATION", 1.5),
            min_position=_float_env("CUTY_FOLLOW_SIM_MIN_POSITION", -1.0),
            max_position=_float_env("CUTY_FOLLOW_SIM_MAX_POSITION", 1.0),
        )


class HeadAdapter(Protocol):
    def set_pan_velocity(self, velocity: float) -> None: ...


class SimulatedHeadAdapter:
    """In-memory actuator in abstract normalized units; never writes hardware."""

    def __init__(self) -> None:
        self.velocity = 0.0
        self.commands = 0

    def set_pan_velocity(self, velocity: float) -> None:
        self.velocity = velocity
        self.commands += 1


@dataclass(frozen=True)
class FollowStatus:
    enabled: bool
    tracking: bool
    x_error: float | None
    y_error: float | None
    pid_output: float
    velocity: float
    simulated_position: float
    reason: str


class _PID:
    def __init__(self, config: FaceFollowConfig) -> None:
        self.kp, self.ki, self.kd = config.kp, config.ki, config.kd
        self.output_limit = config.max_velocity
        self.deadband = config.deadband
        self.derivative_alpha = config.derivative_alpha
        self.integral = 0.0
        self.previous_error: float | None = None
        self.filtered_derivative = 0.0

    def reset_derivative(self) -> None:
        self.previous_error = None
        self.filtered_derivative = 0.0

    def update(self, error: float, dt: float) -> float:
        if abs(error) <= self.deadband:
            error = 0.0
        derivative = 0.0
        if self.previous_error is not None:
            derivative = (error - self.previous_error) / dt
            a = self.derivative_alpha
            self.filtered_derivative += a * (derivative - self.filtered_derivative)
        self.previous_error = error

        candidate_integral = self.integral + error * dt
        unconstrained = self.kp * error + self.ki * candidate_integral + self.kd * self.filtered_derivative
        output = max(-self.output_limit, min(self.output_limit, unconstrained))
        # Conditional integration: accept I only when unsaturated or when the
        # error would drive a saturated output back toward the valid range.
        if output == unconstrained or (unconstrained > output and error < 0) or (unconstrained < output and error > 0):
            self.integral = candidate_integral
        if output != unconstrained:
            output = max(-self.output_limit, min(self.output_limit,
                self.kp * error + self.ki * self.integral + self.kd * self.filtered_derivative))
        return output


class FaceFollowController:
    """One PAN-only, dry-run controller consuming the existing FaceTracker output."""

    def __init__(self, config: FaceFollowConfig, adapter: HeadAdapter | None = None,
                 clock=time.monotonic) -> None:
        if not config.dry_run:
            raise FollowConfigurationError("A physical actuator adapter is not implemented")
        self.config = config
        self.adapter = adapter or SimulatedHeadAdapter()
        self._clock = clock
        self._lock = threading.RLock()
        self._pid = _PID(config)
        self._enabled = config.enabled
        self._last_time: float | None = None
        self._last_target_time: float | None = None
        self._filtered_x: float | None = None
        self._filtered_y: float | None = None
        self._velocity = 0.0
        self._position = 0.0
        self.status = FollowStatus(self._enabled, False, None, None, 0.0, 0.0, 0.0, "disabled")

    def set_enabled(self, enabled: bool) -> None:
        """Internal enable/disable; disable is an immediate command stop."""
        with self._lock:
            self._enabled = bool(enabled)
            self._velocity = 0.0
            self.adapter.set_pan_velocity(0.0)
            self._pid.reset_derivative()
            self._last_time = None
            self.status = FollowStatus(self._enabled, False, None, None, 0.0, 0.0,
                                       self._position, "waiting" if enabled else "manual stop")

    def update(self, target, now: float | None = None) -> FollowStatus:
        with self._lock:
            return self._update(target, now)

    def _update(self, target, now: float | None = None) -> FollowStatus:
        now = self._clock() if now is None else now
        if not self._enabled:
            return self.status
        if target is None or now - target.timestamp >= self.config.lost_timeout:
            self._lose_target()
            return self.status

        if not (math.isfinite(target.x) and math.isfinite(target.y) and
                0 <= target.x <= 1 and 0 <= target.y <= 1):
            self._lose_target("invalid detection")
            return self.status

        a = self.config.detection_alpha
        if self._filtered_x is None:
            self._filtered_x, self._filtered_y = target.x, target.y
        else:
            self._filtered_x += a * (target.x - self._filtered_x)
            self._filtered_y += a * (target.y - self._filtered_y)
        self._last_target_time = target.timestamp
        x_error = self._filtered_x - 0.5
        y_error = self._filtered_y - 0.5

        if self._last_time is None:
            self._last_time = now
            self.status = FollowStatus(True, True, x_error, y_error, 0.0,
                                       self._velocity, self._position, "primed")
            return self.status
        dt = now - self._last_time
        self._last_time = now
        if not math.isfinite(dt) or dt <= 0:
            self._pid.reset_derivative()
            self._velocity = 0.0
            self.adapter.set_pan_velocity(0.0)
            self.status = FollowStatus(True, True, x_error, y_error, 0.0, 0.0,
                                       self._position, "invalid dt; output stopped")
            return self.status
        dt = min(dt, self.config.max_dt)
        output = self._pid.update(x_error, dt)
        max_delta = self.config.max_acceleration * dt
        self._velocity += max(-max_delta, min(max_delta, output - self._velocity))
        self._velocity = max(-self.config.max_velocity, min(self.config.max_velocity, self._velocity))
        next_position = self._position + self._velocity * dt
        self._position = max(self.config.min_position, min(self.config.max_position, next_position))
        if self._position in {self.config.min_position, self.config.max_position}:
            # Prevent the simulator from accumulating a velocity into its stop.
            if (self._position == self.config.max_position and self._velocity > 0) or (
                self._position == self.config.min_position and self._velocity < 0
            ):
                self._velocity = 0.0
        self.adapter.set_pan_velocity(self._velocity)
        self.status = FollowStatus(True, True, x_error, y_error, output, self._velocity,
                                   self._position, "dry-run PAN; vertical error is telemetry only")
        return self.status

    def _lose_target(self, reason: str = "face lost; holding simulated position") -> None:
        was_tracking = self.status.tracking
        self._velocity = 0.0
        self._pid.reset_derivative()
        self._last_time = None
        self._filtered_x = self._filtered_y = None
        if was_tracking:
            self.adapter.set_pan_velocity(0.0)
        self.status = FollowStatus(self._enabled, False, None, None, 0.0, 0.0,
                                   self._position, reason)

