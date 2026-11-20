"""Seguimiento PAN facial con salida separada del control visual.

FaceTracker entrega una coordenada horizontal normalizada; el PID calcula una
velocidad y este controlador integra una posición limitada. El adaptador recibe
esa velocidad y, para hardware, debe convertirla en objetivos STM32, nunca PWM
desde Raspberry. Dry-run es la opción por defecto; el adaptador físico debe
gestionar UART, armado y calibración. Este módulo no incluye una implementación
UART física lista para conectar.
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
    physical_adapter_enabled: bool = False
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
        if self.enabled and not self.dry_run and not self.physical_adapter_enabled:
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
            physical_adapter_enabled=_bool_env("CUTY_FOLLOW_PHYSICAL_ENABLE", False),
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
        """Calcula la corrección PID, limita salida y evita acumulación integral al saturar."""
        if abs(error) <= self.deadband:
            error = 0.0
        derivative = 0.0
        if self.previous_error is not None:
            derivative = (error - self.previous_error) / dt
            a = self.derivative_alpha
            self.filtered_derivative += a * (derivative - self.filtered_derivative)
        self.previous_error = error

        # PID discreto: I integra error·segundos; acepta la integral solo si no satura o ayuda a salir de saturación.
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
    """Controla solo PAN desde FaceTracker; el error vertical no activa un eje TILT."""

    def __init__(self, config: FaceFollowConfig, adapter: HeadAdapter | None = None,
                 clock=time.monotonic) -> None:
        physical_adapter = bool(adapter and getattr(adapter, "is_physical", False))
        if not config.dry_run and not (config.physical_adapter_enabled and physical_adapter):
            raise FollowConfigurationError("Physical follow requires explicit opt-in and a physical adapter")
        if config.dry_run and physical_adapter:
            raise FollowConfigurationError("A physical adapter cannot run under dry-run configuration")
        if physical_adapter and (
            not callable(getattr(adapter, "arm", None)) or
            not callable(getattr(adapter, "stop", None)) or
            not isinstance(getattr(adapter, "is_armed", None), bool)
        ):
            raise FollowConfigurationError("Physical adapter must expose arm(), stop(), and boolean is_armed")
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
        # El adaptador es quien valida calibración, heartbeat y ACK de ARM/START antes de publicar is_armed=True.
        self.status = FollowStatus(
            self._enabled, False, None, None, 0.0, 0.0, 0.0,
            self._mode_reason(tracking=False),
        )

    def _has_physical_adapter(self) -> bool:
        """Detecta el adaptador real sin inferirlo solo por la configuración."""
        return bool(getattr(self.adapter, "is_physical", False))

    def _physical_adapter_is_armed(self) -> bool:
        """El estado activo solo se reporta si el adaptador confirma su armado."""
        return self._has_physical_adapter() and bool(getattr(self.adapter, "is_armed", False))

    def _mode_reason(self, *, tracking: bool) -> str:
        if self._has_physical_adapter():
            if not self._physical_adapter_is_armed():
                return "physical adapter available; disarmed"
            return "physical PAN active" if tracking else "physical PAN armed; waiting for face"
        if self._enabled:
            return "dry-run PAN; vertical error is telemetry only"
        return "simulation disabled"

    def set_enabled(self, enabled: bool) -> None:
        """Activa seguimiento o detiene la salida; el modo físico requiere opt-in y armado."""
        with self._lock:
            if enabled and self._has_physical_adapter():
                arm_adapter = getattr(self.adapter, "arm", None)
                if not callable(arm_adapter) or not arm_adapter() or not self._physical_adapter_is_armed():
                    self._stop_adapter(disarm=True)
                    self._enabled = False
                    self._velocity = 0.0
                    self.status = FollowStatus(False, False, None, None, 0.0, 0.0,
                                               self._position, self._mode_reason(tracking=False))
                    raise FollowConfigurationError("STM32 did not accept explicit ARM/START")
            self._enabled = bool(enabled)
            self._velocity = 0.0
            self._stop_adapter(disarm=not enabled)
            self._pid.reset_derivative()
            self._last_time = None
            self.status = FollowStatus(self._enabled, False, None, None, 0.0, 0.0,
                                       self._position, self._mode_reason(tracking=False)
                                       if self._has_physical_adapter() else
                                       ("dry-run PAN; waiting for face" if enabled else "simulation disabled"))

    def update(self, target, now: float | None = None) -> FollowStatus:
        with self._lock:
            return self._update(target, now)

    def _update(self, target, now: float | None = None) -> FollowStatus:
        now = self._clock() if now is None else now
        if not self._enabled:
            return self.status
        if self._has_physical_adapter() and not self._physical_adapter_is_armed():
            self._stop_adapter(disarm=True)
            self._enabled = False
            self._velocity = 0.0
            self.status = FollowStatus(False, False, None, None, 0.0, 0.0,
                                       self._position, self._mode_reason(tracking=False))
            return self.status
        # Una detección ausente o vencida detiene la salida y desarma adaptadores compatibles.
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
        # El centro de imagen es 0.5; Y queda en estado/telemetría y no mueve un eje reservado.
        x_error = self._filtered_x - 0.5
        y_error = self._filtered_y - 0.5

        if self._last_time is None:
            self._last_time = now
            self.status = FollowStatus(True, True, x_error, y_error, 0.0,
                                       self._velocity, self._position,
                                       self._mode_reason(tracking=True))
            return self.status
        dt = now - self._last_time
        self._last_time = now
        if not math.isfinite(dt) or dt <= 0:
            self._pid.reset_derivative()
            self._velocity = 0.0
            self._stop_adapter(disarm=True)
            if self._has_physical_adapter():
                self._enabled = False
                reason = self._mode_reason(tracking=False)
            else:
                reason = "dry-run PAN; invalid dt; output stopped"
            self.status = FollowStatus(self._enabled, False, x_error, y_error, 0.0, 0.0,
                                       self._position, reason)
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
        # La Raspberry entrega velocidad normalizada; la trayectoria física corresponde al STM32.
        self.adapter.set_pan_velocity(self._velocity)
        self.status = FollowStatus(True, True, x_error, y_error, output, self._velocity,
                                   self._position, self._mode_reason(tracking=True))
        return self.status

    def _lose_target(self, reason: str | None = None) -> None:
        was_tracking = self.status.tracking
        self._velocity = 0.0
        self._pid.reset_derivative()
        self._last_time = None
        self._filtered_x = self._filtered_y = None
        if was_tracking or self._has_physical_adapter():
            self._stop_adapter(disarm=True)
        if self._has_physical_adapter():
            # Para reanudar tras perder la cara, exige otra acción explícita de armado.
            self._enabled = False
        if reason is None:
            reason = ("physical adapter available; disarmed" if self._has_physical_adapter()
                      else "face lost; holding simulated position")
        elif self._has_physical_adapter():
            reason = f"physical adapter available; disarmed ({reason})"
        else:
            reason = f"dry-run PAN; {reason}"
        self.status = FollowStatus(self._enabled, False, None, None, 0.0, 0.0,
                                   self._position, reason)

    def _stop_adapter(self, *, disarm: bool) -> None:
        stop = getattr(self.adapter, "stop", None) if disarm else None
        if callable(stop):
            stop()
        else:
            self.adapter.set_pan_velocity(0.0)

