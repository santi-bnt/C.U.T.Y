"""Ejecutor de objetivos V2 y gestos coordinados usando una calibración validada."""
from __future__ import annotations

import time
import threading

from .calibration_profile import RobotCalibration
from .motion_actions import MotionAction, POSES
from .robot_commands import RobotTelemetry, command, parse_response, parse_telemetry, target
from .stm32_bridge import STM32Bridge

AXES = ("HEAD_PAN", "LEFT_ARM", "RIGHT_ARM")
STEP_SECONDS = 0.25


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
        self.connected = False
        self.enabled = False
        self._last_sequence: int | None = None
        self._io_lock = threading.RLock()
        self._telemetry: RobotTelemetry | None = None
        self._telemetry_received_at: float | None = None
        self._last_state = "UNKNOWN"
        self._monitor_stop = threading.Event()
        self._monitor_thread = None
        self._active = False
        self._owner_lock = threading.Lock()
        self._motion_owner: str | None = None
        self._motion_lock = threading.RLock()
        self._motion_cancel = threading.Event()
        self._stopping = threading.Event()
        self._motion_generation = 0

    def enable(self) -> bool:
        """Verifica enlace y perfil; no arma ni inicia el movimiento físico."""
        if self.enabled:
            return True
        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            return False
        try:
            self._connect(require_disarmed=True, authorize=True)
        except (OSError, RuntimeError, ConnectionError, TimeoutError):
            # El monitor puede recuperar el enlace, pero la puerta de movimiento
            # requiere que el llamador vuelva a autorizar la sesión explícitamente.
            self._monitor_stop.clear()
            self._start_monitor()
            return False
        self._monitor_stop.clear()
        self._motion_cancel.clear()
        self._start_monitor()
        return True

    def _connect(self, *, require_disarmed: bool, authorize: bool) -> None:
        bridge = self._bridge_factory(self._port)
        self._last_sequence = None
        try:
            state = self._exchange(bridge, "V2,HB")
            if state != "DISARMED":
                if not require_disarmed and state in {"READY", "ACTIVE"}:
                    state = self._exchange(bridge, "V2,DISARM", expected="DISARMED")
                else:
                    raise RuntimeError(
                        f"STM32 debe estar DISARMED para habilitar control local (estado {state})"
                    )
        except Exception:
            bridge.close()
            raise
        self._bridge = bridge
        self.connected = True
        self.enabled = authorize
        self._last_sequence = None

    def disable(self) -> None:
        """Cancela trayectorias, intenta DISARM y libera UART."""
        self._motion_generation += 1
        self._motion_cancel.set()
        self._stopping.set()
        self._monitor_stop.set()
        worker = self._monitor_thread
        self._monitor_thread = None
        if worker is not None and worker is not threading.current_thread():
            worker.join(timeout=1.2)
        with self._motion_lock:
            try:
                self.stop()
            except Exception:
                # Si el enlace no acepta DISARM, cerrar UART deja actuar el watchdog local.
                pass
            finally:
                self._drop_link()
                self._stopping.clear()

    def _drop_link(self) -> None:
        bridge, self._bridge = self._bridge, None
        self.connected = False
        self.enabled = False
        self._active = False
        self._last_sequence = None
        with self._owner_lock:
            self._motion_owner = None
        if bridge is not None:
            try:
                bridge.close()
            except Exception:
                pass

    def stop(self) -> None:
        # Incrementa antes de esperar el lock para interrumpir una secuencia en curso.
        self._motion_generation += 1
        generation = self._motion_generation
        self._motion_cancel.set()
        self._stopping.set()
        with self._motion_lock:
            try:
                if self.enabled and self._bridge is not None:
                    bridge = self._require_enabled()
                    self._exchange(bridge, "V2,DISARM")
            except Exception:
                self._drop_link()
                raise
            finally:
                self._active = False
                with self._owner_lock:
                    self._motion_owner = None
                if generation == self._motion_generation:
                    self._stopping.clear()

    def execute(self, action: MotionAction) -> dict[str, object]:
        if not isinstance(action, MotionAction):
            raise ValueError("Acción de movimiento no permitida")
        if action is MotionAction.STOP:
            self.stop()
            return {"accepted": True, "action": action.value, "mode": "stopped"}
        if action not in POSES:
            raise ValueError("Acción sin trayectoria implementada")
        if not self.enabled or not self.connected:
            raise RuntimeError("Movimiento desautorizado hasta revalidar el enlace localmente")
        generation = self._motion_generation
        if not self.claim("voice"):
            raise RuntimeError("Otro controlador posee los ejes físicos")
        try:
            with self._motion_lock:
                if generation != self._motion_generation or self._stopping.is_set():
                    return {"accepted": False, "action": action.value,
                            "mode": "robot", "reason": "cancelled by stop"}
                self._motion_cancel.clear()
                bridge = self._require_enabled()
                if not self.activate(_generation=generation):
                    return {"accepted": False, "action": action.value,
                            "mode": "robot", "reason": "cancelled by stop"}
                for keyframe in POSES[action]:
                    if self._motion_cancelled(generation):
                        return {"accepted": False, "action": action.value,
                                "mode": "robot", "reason": "cancelled by stop"}
                    # Actualiza todos los ejes del fotograma antes de avanzar.
                    for axis, position in keyframe.items():
                        if self._motion_cancelled(generation):
                            return {"accepted": False, "action": action.value,
                                    "mode": "robot", "reason": "cancelled by stop"}
                        self.set_axis_target(
                            axis, round(position * 1000), owner="voice", _generation=generation,
                        )
                    if self._sleep is time.sleep:
                        cancelled = self._motion_cancel.wait(STEP_SECONDS)
                    else:
                        self._sleep(STEP_SECONDS)
                        cancelled = self._motion_cancelled(generation)
                    if cancelled or self._motion_cancelled(generation):
                        return {"accepted": False, "action": action.value,
                                "mode": "robot", "reason": "cancelled by stop"}
                return {"accepted": True, "action": action.value, "mode": "robot"}
        except Exception:
            self._drop_link()
            raise
        finally:
            self.release("voice")

    def activate(self, *, _generation: int | None = None) -> bool:
        """Arma explícitamente desde DISARMED y deja el heartbeat supervisor activo."""
        explicit_request = _generation is None
        generation = self._motion_generation if explicit_request else _generation
        with self._motion_lock:
            if generation != self._motion_generation or self._stopping.is_set():
                return False
            if explicit_request:
                self._motion_cancel.clear()
            elif self._motion_cancelled(generation):
                return False
            bridge = self._require_enabled()
            try:
                self._ensure_active(bridge, generation)
                return not self._motion_cancelled(generation)
            except Exception:
                self._drop_link()
                raise

    def set_axis_target(
        self, axis: str, milli_units: int, *, owner: str = "voice",
        _generation: int | None = None,
    ) -> bool:
        """Reemplaza el objetivo actual de un eje; el STM32 mailbox descarta objetivos viejos."""
        if axis not in self.profile or isinstance(milli_units, bool) or not isinstance(milli_units, int):
            raise ValueError("Eje o consigna inválidos")
        if not -1000 <= milli_units <= 1000:
            raise ValueError("La consigna normalizada debe estar entre -1000 y 1000")
        with self._owner_lock:
            if self._motion_owner != owner:
                raise RuntimeError("El controlador no posee autorización exclusiva de movimiento")
        generation = self._motion_generation if _generation is None else _generation
        with self._motion_lock:
            if self._stopping.is_set() or self._motion_cancelled(generation):
                return False
            bridge = self._require_enabled()
            try:
                self._ensure_active(bridge, generation)
                if self._motion_cancelled(generation):
                    return False
                self._exchange(bridge, "V2,HB", expected="ACTIVE")
                if self._motion_cancelled(generation):
                    return False
                self._exchange(bridge, target(axis, milli_units), expected="ACTIVE")
                return not self._motion_cancelled(generation)
            except Exception:
                self._drop_link()
                raise

    def _motion_cancelled(self, generation: int) -> bool:
        return generation != self._motion_generation or self._motion_cancel.is_set()

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

    def status_snapshot(self) -> dict[str, object]:
        """Devuelve observabilidad de solo lectura; nunca informa posición medida."""
        with self._io_lock:
            telemetry = self._telemetry
            age = (
                max(0.0, self._clock() - self._telemetry_received_at)
                if self._telemetry_received_at is not None else None
            )
            telemetry_fresh = age is not None and age <= 1.0
            return {
                "connection": "connected" if self.connected else "offline",
                "mode": "robot",
                "safety_state": (
                    telemetry.state if self.connected and telemetry_fresh and telemetry
                    else self._last_state if self.connected else "UNKNOWN"
                ),
                "last_known_state": self._last_state,
                "motion_authorized": self.enabled,
                "controller_active": bool(self.enabled and self._active),
                "physical_output_status": "unverified",
                "firmware_profile_match": "unverified",
                "telemetry_age_seconds": age,
                "telemetry_fresh": telemetry_fresh,
                "position_kind": "commanded",
                "measured_positions_available": False,
                "commanded_milli_units": (
                    dict(telemetry.commanded_milli_units) if telemetry else None
                ),
                "rx_errors": telemetry.rx_errors if telemetry else None,
                "dropped_tx": telemetry.dropped_tx if telemetry else None,
                "uart_status": telemetry.uart_status if telemetry else None,
            }

    def _ensure_active(self, bridge, generation: int) -> None:
        if self._motion_cancelled(generation):
            return
        if self._active:
            return
        state = self._exchange(bridge, "V2,HB")
        if self._motion_cancelled(generation):
            return
        if state == "DISARMED":
            self._exchange(bridge, "V2,ARM", expected="READY")
            if self._motion_cancelled(generation):
                return
            self._exchange(bridge, "V2,START", expected="ACTIVE")
        elif state != "ACTIVE":
            raise RuntimeError(f"No se inicia movimiento desde estado {state}")
        if not self._motion_cancelled(generation):
            self._active = True

    def _start_monitor(self) -> None:
        worker = self._monitor_thread
        if worker is not None and worker.is_alive():
            return
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, name="cuty-motion-link-monitor", daemon=True,
        )
        self._monitor_thread.start()

    def _require_enabled(self):
        if not self.connected or not self.enabled or self._bridge is None:
            raise RuntimeError("Controlador físico deshabilitado localmente")
        return self._bridge

    def _monitor_loop(self) -> None:
        while not self._monitor_stop.wait(0.15):
            if not self.connected:
                if self._monitor_stop.wait(0.85):
                    return
                try:
                    # Reconectar solo observa DISARMED; READY/ACTIVE se desarman,
                    # y FAULT requiere recuperación explícita fuera del monitor.
                    self._connect(require_disarmed=False, authorize=False)
                except (OSError, RuntimeError, ConnectionError, TimeoutError, ValueError):
                    continue
                continue
            try:
                # HB en DISARMED solo mantiene enlace/telemetría; nunca arma.
                self._exchange(self._bridge, "V2,HB")
            except Exception:
                # Se cierra la sesión y se vuelve a intentar sin reanudar objetivos.
                self._drop_link()

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
            self._last_state = state
            drain_events = getattr(bridge, "drain_events", None)
            if drain_events is not None:
                for event in drain_events():
                    try:
                        if event.kind == "TELEM":
                            self._telemetry = parse_telemetry(event)
                            self._telemetry_received_at = self._clock()
                        elif event.kind == "STATE" and len(event.fields) == 2:
                            if event.fields[0] in {"DISARMED", "READY", "ACTIVE", "FAULT"}:
                                self._last_state = event.fields[0]
                    except ValueError:
                        # Un registro de diagnóstico malformado no autoriza movimiento.
                        continue
            if expected is not None and state != expected:
                raise RuntimeError(f"Estado STM32 {state}; se esperaba {expected}")
            return state
