"""Lista cerrada e intérprete determinista de solicitudes de movimiento por voz.

Este módulo convierte texto en acciones semánticas; nunca genera PWM ni UART.
La ejecución pertenece a un controlador con modo físico y calibración validados.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
import threading
import time
import unicodedata

from .calibration_profile import RobotCalibration


class MotionAction(str, Enum):
    STOP = "stop"
    WAVE_LEFT = "wave_left"
    WAVE_RIGHT = "wave_right"
    WAVE_BOTH = "wave_both"
    HEAD_LEFT = "head_left"
    HEAD_RIGHT = "head_right"
    HEAD_CENTER = "head_center"
    ARM_LEFT = "arm_left"
    ARM_RIGHT = "arm_right"
    GREET_RIGHT = "greet_right"


class OperationMode(str, Enum):
    SIMULATION = "simulation"
    TEST = "test"
    ROBOT = "robot"


# Referencias normalizadas al centro calibrado; no representan grados reales.
POSES = {
    MotionAction.HEAD_LEFT: ({"HEAD_PAN": -0.15},),
    MotionAction.HEAD_RIGHT: ({"HEAD_PAN": 0.15},),
    MotionAction.HEAD_CENTER: ({"HEAD_PAN": 0.0},),
    MotionAction.ARM_LEFT: ({"LEFT_ARM": 0.20},),
    MotionAction.ARM_RIGHT: ({"RIGHT_ARM": 0.20},),
    MotionAction.GREET_RIGHT: (
        {"HEAD_PAN": 0.12, "LEFT_ARM": 0.15, "RIGHT_ARM": 0.15},
        {"HEAD_PAN": 0.0, "LEFT_ARM": 0.0, "RIGHT_ARM": 0.0},
    ),
    MotionAction.WAVE_LEFT: (
        {"LEFT_ARM": 0.20}, {"LEFT_ARM": 0.08}, {"LEFT_ARM": 0.20}, {"LEFT_ARM": 0.0},
    ),
    MotionAction.WAVE_RIGHT: (
        {"RIGHT_ARM": 0.20}, {"RIGHT_ARM": 0.08}, {"RIGHT_ARM": 0.20}, {"RIGHT_ARM": 0.0},
    ),
    MotionAction.WAVE_BOTH: (
        {"LEFT_ARM": 0.20, "RIGHT_ARM": 0.20},
        {"LEFT_ARM": 0.08, "RIGHT_ARM": 0.08},
        {"LEFT_ARM": 0.20, "RIGHT_ARM": 0.20},
        {"LEFT_ARM": 0.0, "RIGHT_ARM": 0.0},
    ),
}
SIMULATION_STEP_SECONDS = 0.25


@dataclass(frozen=True)
class MotionRequest:
    action: MotionAction


_PHRASES = {
    "detente": MotionAction.STOP,
    "para": MotionAction.STOP,
    "saluda": MotionAction.WAVE_RIGHT,
    "saluda con el brazo izquierdo": MotionAction.WAVE_LEFT,
    "saluda con el brazo derecho": MotionAction.WAVE_RIGHT,
    "saluda con ambos brazos": MotionAction.WAVE_BOTH,
    "saluda y mira a la derecha": MotionAction.GREET_RIGHT,
    "levanta el brazo izquierdo": MotionAction.ARM_LEFT,
    "levanta el brazo derecho": MotionAction.ARM_RIGHT,
    "mueve la cabeza a la izquierda": MotionAction.HEAD_LEFT,
    "mira a la izquierda": MotionAction.HEAD_LEFT,
    "mueve la cabeza a la derecha": MotionAction.HEAD_RIGHT,
    "mira a la derecha": MotionAction.HEAD_RIGHT,
    "regresa al centro": MotionAction.HEAD_CENTER,
}


def _normalize(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text.casefold())
    plain = "".join(char for char in folded if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", plain).strip()


def parse_motion_request(text: str) -> MotionRequest:
    """Acepta solo frases completas del allowlist; Stop tiene prioridad explícita."""
    if not isinstance(text, str) or not text.strip() or len(text) > 240:
        raise ValueError("Solicitud de movimiento vacía o demasiado larga")
    normalized = _normalize(text)
    normalized = re.sub(r"^cuty\s+", "", normalized)
    # En una transcripción con otras palabras, cualquier detención explícita gana.
    if re.search(r"\b(detente|para|alto|stop)\b", normalized):
        return MotionRequest(MotionAction.STOP)
    action = _PHRASES.get(normalized)
    if action is None:
        raise ValueError("Solicitud ambigua o fuera de las acciones permitidas")
    return MotionRequest(action)


class MotionActionGate:
    """Puerta con modos explícitos; solo TEST y ROBOT pueden abrir el enlace físico."""

    def __init__(self, executor=None) -> None:
        self._executor = executor
        self._mode = OperationMode.SIMULATION
        self._test_axis: str | None = None
        self._simulation_positions = {"HEAD_PAN": 0, "LEFT_ARM": 0, "RIGHT_ARM": 0}
        self._simulation_start_positions = dict(self._simulation_positions)
        self._simulation_frames: tuple[dict[str, float], ...] = ()
        self._simulation_started_at: float | None = None
        self._simulation_active = False
        self._simulation_lock = threading.RLock()

    @property
    def mode(self) -> OperationMode:
        return self._mode

    @property
    def physical_enabled(self) -> bool:
        return self._mode in {OperationMode.TEST, OperationMode.ROBOT}

    def enable_physical(self, *, calibration: RobotCalibration | None) -> None:
        """Compatibilidad: habilitar operación completa equivale al modo ROBOT."""
        self._enable(calibration=calibration, mode=OperationMode.ROBOT)

    def enable_test(self, *, axis: str, calibration: RobotCalibration | None) -> None:
        """Habilita órdenes de una sola articulación ya calibrada para una prueba corta."""
        if axis not in {"HEAD_PAN", "LEFT_ARM", "RIGHT_ARM"}:
            raise RuntimeError("El modo PRUEBA requiere seleccionar un eje válido")
        self._enable(calibration=calibration, mode=OperationMode.TEST, axis=axis)

    def _enable(
        self, *, calibration: RobotCalibration | None, mode: OperationMode,
        axis: str | None = None,
    ) -> None:
        if self._mode is not OperationMode.SIMULATION and self._mode is not mode:
            raise RuntimeError("Vuelve a SIMULATION y desarma antes de cambiar el modo físico")
        try:
            if calibration is None:
                raise ValueError("perfil ausente")
            calibration.validate_complete()
        except (AttributeError, TypeError, ValueError) as exc:
            raise RuntimeError("Movimiento físico requiere calibración completa y válida") from exc
        if self._executor is None:
            raise RuntimeError("Movimiento físico requiere un ejecutor")
        enable = getattr(self._executor, "enable", None)
        if not callable(enable) or enable() is not True:
            raise RuntimeError("El ejecutor no confirmó el enlace y el estado seguro")
        self._mode = mode
        self._test_axis = axis

    def disable_physical(self) -> None:
        self._mode = OperationMode.SIMULATION
        self._test_axis = None
        if self._executor is not None:
            self._executor.disable()

    def select_simulation(self) -> None:
        """Desarma y cierra el enlace antes de volver a la simulación."""
        self.disable_physical()

    def submit(self, request: MotionRequest) -> dict[str, object]:
        if not isinstance(request, MotionRequest):
            raise TypeError("Se requiere una MotionRequest validada")
        if request.action is MotionAction.STOP:
            if self.physical_enabled and self._executor is not None:
                self._executor.stop()
            self._stop_simulation()
            return {"accepted": True, "action": request.action.value, "mode": self._mode.value}
        if self._mode is OperationMode.SIMULATION:
            frames = POSES.get(request.action)
            if frames is None:
                return {"accepted": False, "action": request.action.value,
                        "mode": self._mode.value, "reason": "action has no simulated pose"}
            with self._simulation_lock:
                now = time.monotonic()
                self._advance_simulation(now)
                self._simulation_start_positions = dict(self._simulation_positions)
                self._simulation_frames = frames
                self._simulation_started_at = now
                self._simulation_active = True
                target_positions = dict(self._simulation_positions)
                for frame in frames:
                    for axis, position in frame.items():
                        target_positions[axis] = round(position * 1000)
            return {
                "accepted": True,
                "action": request.action.value,
                "mode": self._mode.value,
                "simulated": True,
                "commanded_milli_units": target_positions,
            }
        if not self.physical_enabled:
            return {"accepted": False, "action": request.action.value,
                    "mode": self._mode.value, "reason": "physical motion is not enabled"}
        if self._mode is OperationMode.TEST and not self._test_action_allowed(request.action):
            return {"accepted": False, "action": request.action.value,
                    "mode": self._mode.value, "reason": "action exceeds the selected test axis"}
        return self._executor.execute(request.action)

    def _test_action_allowed(self, action: MotionAction) -> bool:
        axis_actions = {
            "HEAD_PAN": {MotionAction.HEAD_LEFT, MotionAction.HEAD_RIGHT, MotionAction.HEAD_CENTER},
            "LEFT_ARM": {MotionAction.ARM_LEFT, MotionAction.WAVE_LEFT},
            "RIGHT_ARM": {MotionAction.ARM_RIGHT, MotionAction.WAVE_RIGHT},
        }
        return action in axis_actions.get(self._test_axis, set())

    def status_snapshot(self) -> dict[str, object]:
        """Expone referencias del modo activo y nunca las presenta como posición medida."""
        snapshot = {}
        get_snapshot = getattr(self._executor, "status_snapshot", None)
        if callable(get_snapshot):
            snapshot = get_snapshot()
        base = {
            "connection": "offline",
            "safety_state": "UNKNOWN",
            "last_known_state": "UNKNOWN",
            "motion_authorized": False,
            "controller_active": False,
            "physical_output_status": "unverified",
            "firmware_profile_match": "unverified",
            "telemetry_fresh": False,
            "position_kind": "commanded",
            "measured_positions_available": False,
            "commanded_milli_units": None,
            "rx_errors": None,
            "dropped_tx": None,
            "uart_status": None,
        }
        base.update(snapshot)
        base["mode"] = self._mode.value
        if self._mode is OperationMode.SIMULATION:
            with self._simulation_lock:
                self._advance_simulation(time.monotonic())
                commanded = dict(self._simulation_positions)
                active = self._simulation_active
            base["motion_authorized"] = False
            base["controller_active"] = active
            base["commanded_milli_units"] = commanded
        return base

    def _stop_simulation(self) -> None:
        with self._simulation_lock:
            self._advance_simulation(time.monotonic())
            self._simulation_frames = ()
            self._simulation_started_at = None
            self._simulation_active = False

    def _advance_simulation(self, now: float) -> None:
        """Interpola fotogramas en tiempo de consulta, sin bloquear voz ni telemetría."""
        started = self._simulation_started_at
        if not self._simulation_active or started is None or not self._simulation_frames:
            return
        elapsed = max(0.0, now - started)
        completed_frames = int(elapsed / SIMULATION_STEP_SECONDS)
        if completed_frames >= len(self._simulation_frames):
            positions = dict(self._simulation_start_positions)
            for frame in self._simulation_frames:
                for axis, value in frame.items():
                    positions[axis] = round(value * 1000)
            self._simulation_positions = positions
            self._simulation_active = False
            self._simulation_frames = ()
            self._simulation_started_at = None
            return

        segment_start = dict(self._simulation_start_positions)
        for frame in self._simulation_frames[:completed_frames]:
            for axis, value in frame.items():
                segment_start[axis] = round(value * 1000)
        segment_target = dict(segment_start)
        for axis, value in self._simulation_frames[completed_frames].items():
            segment_target[axis] = round(value * 1000)
        fraction = (elapsed % SIMULATION_STEP_SECONDS) / SIMULATION_STEP_SECONDS
        self._simulation_positions = {
            axis: round(start + (segment_target[axis] - start) * fraction)
            for axis, start in segment_start.items()
        }
