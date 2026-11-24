"""Ejecutor de objetivos V2 y gestos coordinados usando una calibración validada."""
from __future__ import annotations

import time
import threading

from .calibration_profile import RobotCalibration
from .motion_actions import MotionAction
from .robot_commands import command, parse_response, target
from .stm32_bridge import STM32Bridge

AXES = ("HEAD_PAN", "LEFT_ARM", "RIGHT_ARM")
STEP_SECONDS = 0.25

# Posiciones normalizadas pequeñas dentro del recorrido confirmado por eje.
POSES = {
    MotionAction.HEAD_LEFT: ({"HEAD_PAN": -0.15},),
    MotionAction.HEAD_RIGHT: ({"HEAD_PAN": 0.15},),
    MotionAction.HEAD_CENTER: ({"HEAD_PAN": 0.0},),
    MotionAction.ARM_LEFT: ({"LEFT_ARM": 0.20},),
    MotionAction.ARM_RIGHT: ({"RIGHT_ARM": 0.20},),
    MotionAction.WAVE_LEFT: ({"LEFT_ARM": 0.20}, {"LEFT_ARM": 0.08}, {"LEFT_ARM": 0.20}, {"LEFT_ARM": 0.0}),
    MotionAction.WAVE_RIGHT: ({"RIGHT_ARM": 0.20}, {"RIGHT_ARM": 0.08}, {"RIGHT_ARM": 0.20}, {"RIGHT_ARM": 0.0}),
    MotionAction.WAVE_BOTH: (
        {"LEFT_ARM": 0.20, "RIGHT_ARM": 0.20},
        {"LEFT_ARM": 0.08, "RIGHT_ARM": 0.08},
        {"LEFT_ARM": 0.20, "RIGHT_ARM": 0.20},
        {"LEFT_ARM": 0.0, "RIGHT_ARM": 0.0},
    ),
}


class RobotMotionExecutor:
    """Sesión UART única; el llamador controla su autorización física local."""

    def __init__(self, port: str, calibration: RobotCalibration, *, bridge_factory=STM32Bridge,
                 clock=time.monotonic, sleep=time.sleep) -> None:
        calibration.validate_complete()
        self.profile = {axis.axis: axis for axis in calibration.axes}
        self._bridge_factory = bridge_factory
        self._clock = clock
        self._sleep = sleep
        self._bridge = None
        self._port = port
        self.enabled = False
        self._last_sequence: int | None = None
        self._io_lock = threading.RLock()
        self._heartbeat_stop = threading.Event()
        self._heartbeat_thread = None
        self._active = False
        self._owner_lock = threading.Lock()
        self._motion_owner: str | None = None

    def enable(self) -> bool:
        """Verifica enlace y perfil; no arma ni inicia el movimiento físico."""
        if self.enabled:
            return True
        bridge = self._bridge_factory(self._port)
        try:
            state = self._exchange(bridge, "V2,HB")
            if state != "DISARMED":
                raise RuntimeError(f"STM32 debe estar DISARMED para habilitar control local (estado {state})")
        except Exception:
            bridge.close()
            raise
        self._bridge = bridge
        self.enabled = True
        self._last_sequence = None
        return True

    def disable(self) -> None:
        """Desarma y libera UART, incluso después de un error de comunicación."""
        bridge, self._bridge = self._bridge, None
        self.enabled = False
        self._active = False
        self._heartbeat_stop.set()
        worker = self._heartbeat_thread
        self._heartbeat_thread = None
        if worker is not None and worker is not threading.current_thread():
            worker.join(timeout=0.6)
        self._last_sequence = None
        with self._owner_lock:
            self._motion_owner = None
        if bridge is not None:
            bridge.close()

    def stop(self) -> None:
        if not self.enabled or self._bridge is None:
            self._active = False
            return
        bridge = self._require_enabled()
        self._heartbeat_stop.set()
        worker = self._heartbeat_thread
        self._heartbeat_thread = None
        if worker is not None and worker is not threading.current_thread():
            worker.join(timeout=0.6)
        try:
            self._exchange(bridge, "V2,DISARM")
        except Exception:
            self.disable()
            raise
        self._active = False
        with self._owner_lock:
            self._motion_owner = None

    def execute(self, action: MotionAction) -> dict[str, object]:
        if not isinstance(action, MotionAction):
            raise ValueError("Acción de movimiento no permitida")
        if action is MotionAction.STOP:
            self.stop()
            return {"accepted": True, "action": action.value, "mode": "stopped"}
        if action not in POSES:
            raise ValueError("Acción sin trayectoria implementada")
        if not self.claim("voice"):
            raise RuntimeError("Otro controlador posee los ejes físicos")
        bridge = None
        try:
            bridge = self._require_enabled()
            self.activate()
            for keyframe in POSES[action]:
                # Actualiza todos los ejes del fotograma antes de avanzar al siguiente.
                for axis, position in keyframe.items():
                    self.set_axis_target(axis, round(position * 1000), owner="voice")
                self._sleep(STEP_SECONDS)
            return {"accepted": True, "action": action.value, "mode": "hardware"}
        except Exception:
            self.disable()
            raise
        finally:
            self.release("voice")

    def activate(self) -> bool:
        """Arma explícitamente desde DISARMED y deja el heartbeat supervisor activo."""
        bridge = self._require_enabled()
        try:
            self._ensure_active(bridge)
            return True
        except Exception:
            self.disable()
            raise

    def set_axis_target(self, axis: str, milli_units: int, *, owner: str = "voice") -> bool:
        """Reemplaza el objetivo actual de un eje; el STM32 mailbox descarta objetivos viejos."""
        if axis not in self.profile or isinstance(milli_units, bool) or not isinstance(milli_units, int):
            raise ValueError("Eje o consigna inválidos")
        if not -1000 <= milli_units <= 1000:
            raise ValueError("La consigna normalizada debe estar entre -1000 y 1000")
        with self._owner_lock:
            if self._motion_owner != owner:
                raise RuntimeError("El controlador no posee autorización exclusiva de movimiento")
        bridge = self._require_enabled()
        try:
            self._ensure_active(bridge)
            self._exchange(bridge, "V2,HB", expected="ACTIVE")
            self._exchange(bridge, target(axis, milli_units), expected="ACTIVE")
            return True
        except Exception:
            self.disable()
            raise

    def claim(self, owner: str) -> bool:
        if owner not in {"voice", "face_follow"}:
            return False
        with self._owner_lock:
            if self._motion_owner not in {None, owner}:
                return False
            self._motion_owner = owner
            return True

    def release(self, owner: str) -> None:
        with self._owner_lock:
            if self._motion_owner == owner:
                self._motion_owner = None

    def _ensure_active(self, bridge) -> None:
        if self._active:
            return
        state = self._exchange(bridge, "V2,HB")
        if state == "DISARMED":
            self._exchange(bridge, "V2,ARM", expected="READY")
            self._exchange(bridge, "V2,START", expected="ACTIVE")
        elif state != "ACTIVE":
            raise RuntimeError(f"No se inicia movimiento desde estado {state}")
        self._active = True
        self._heartbeat_stop.clear()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, name="cuty-motion-heartbeat", daemon=True,
        )
        self._heartbeat_thread.start()

    def _require_enabled(self):
        if not self.enabled or self._bridge is None:
            raise RuntimeError("Controlador físico deshabilitado localmente")
        return self._bridge

    def _heartbeat_loop(self) -> None:
        while not self._heartbeat_stop.wait(0.15):
            if not self._active or not self.enabled:
                return
            try:
                self._exchange(self._require_enabled(), "V2,HB", expected="ACTIVE")
            except Exception:
                # Un heartbeat perdido invalida la sesión; liberar UART sin rearmado automático.
                self.disable()
                return

    def _exchange(self, bridge, wire: bytes | str, *, expected: str | None = None) -> str:
        if isinstance(wire, str):
            wire = command(wire)
        with self._io_lock:
            response = parse_response(bridge.exchange(wire, timeout=0.4))
            if response.kind != "ACK" or len(response.fields) != 3:
                raise RuntimeError("STM32 rechazó o devolvió una respuesta UART inválida")
            sequence, result, state = response.fields
            if not sequence.isascii() or not sequence.isdigit() or result != "OK":
                raise RuntimeError("ACK V2 inválido")
            sequence_number = int(sequence)
            if self._last_sequence is not None and sequence_number != self._last_sequence + 1:
                raise RuntimeError("Secuencia UART perdida; se cancela el movimiento")
            self._last_sequence = sequence_number
            if expected is not None and state != expected:
                raise RuntimeError(f"Estado STM32 {state}; se esperaba {expected}")
            return state
