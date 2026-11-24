"""Lista cerrada e intérprete determinista de solicitudes de movimiento por voz.

Este módulo convierte texto en acciones semánticas; nunca genera PWM ni UART.
La ejecución pertenece a un controlador con modo físico y calibración validados.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
import unicodedata


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
    """Puerta de ejecución; parte en simulación y exige habilitación manual."""

    def __init__(self, executor=None) -> None:
        self._executor = executor
        self._physical_enabled = False

    @property
    def physical_enabled(self) -> bool:
        return self._physical_enabled

    def enable_physical(self, *, link_valid: bool, calibration_complete: bool) -> None:
        if not link_valid or not calibration_complete or self._executor is None:
            raise RuntimeError("Movimiento físico requiere enlace, calibración completa y ejecutor")
        self._physical_enabled = True

    def disable_physical(self) -> None:
        self._physical_enabled = False
        if self._executor is not None:
            self._executor.stop()

    def submit(self, request: MotionRequest) -> dict[str, object]:
        if not isinstance(request, MotionRequest):
            raise TypeError("Se requiere una MotionRequest validada")
        if request.action is MotionAction.STOP:
            if self._executor is not None:
                self._executor.stop()
            return {"accepted": True, "action": request.action.value, "mode": "stopped"}
        if not self._physical_enabled:
            return {"accepted": False, "action": request.action.value,
                    "mode": "simulation", "reason": "physical motion is not enabled"}
        return self._executor.execute(request.action)
