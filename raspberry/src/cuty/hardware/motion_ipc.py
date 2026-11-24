"""IPC local entre FaceTracker (pantalla) y el único dueño Raspberry del UART."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import socket
import threading
import time

try:
    import pwd
except ImportError:  # pragma: no cover - el módulo no existe en Windows
    pwd = None


def motion_socket_path() -> Path:
    if os.name == "posix":
        try:
            if pwd is None:
                raise ImportError
            uid = pwd.getpwnam(os.getenv("CUTY_RUNTIME_USER", "santi")).pw_uid
            default = f"/run/user/{uid}/cuty-motion.sock"
        except (KeyError, ImportError):
            uid = os.getuid() if hasattr(os, "getuid") else 0
            default = f"/tmp/cuty-motion-{uid}.sock"
    else:
        default = str(Path.home() / ".cache" / "cuty-motion.sock")
    return Path(os.getenv("CUTY_MOTION_SOCKET", default))


class MotionIpcServer:
    """Servidor local; solo acepta al launcher root o al usuario de la aplicación."""

    def __init__(self, executor, enabled: bool, path: str | Path | None = None) -> None:
        self.executor = executor
        self.enabled = bool(enabled)
        self.path = Path(path) if path is not None else motion_socket_path()
        self._socket = None
        self._stop = threading.Event()
        self._thread = None
        self._follow_active = False
        self._position = 0.0
        self._last_update = None

    def start(self) -> None:
        if os.name != "posix" or not hasattr(socket, "SO_PEERCRED"):
            raise OSError("El enlace de movimiento requiere credenciales Unix locales")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists() or self.path.is_symlink():
            if not self.path.is_socket():
                raise OSError(f"La ruta IPC existe y no es un socket: {self.path}")
            self.path.unlink()
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            listener.bind(str(self.path))
            os.chmod(self.path, 0o600)
            listener.listen(4)
            listener.settimeout(0.25)
            self._socket = listener
            self._thread = threading.Thread(target=self._serve, daemon=True, name="cuty-motion-ipc")
            self._thread.start()
        except Exception:
            listener.close()
            if self.path.is_socket():
                self.path.unlink()
            raise

    def _serve(self) -> None:
        while not self._stop.is_set():
            try:
                connection, _ = self._socket.accept()
            except (TimeoutError, socket.timeout):
                continue
            except OSError:
                break
            with connection:
                connection.settimeout(0.2)
                try:
                    _, uid, _ = __import__("struct").unpack(
                        "3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12),
                    )
                    if uid not in {0, os.getuid()}:
                        raise PermissionError("Cliente IPC no autorizado")
                    raw = connection.recv(513)
                    if not raw or len(raw) > 512:
                        raise ValueError("Mensaje IPC inválido")
                    request = json.loads(raw.decode("utf-8"))
                    response = self._handle(request)
                except Exception as error:
                    response = {"ok": False, "error": str(error)[:160]}
                try:
                    connection.sendall(json.dumps(response, separators=(",", ":")).encode("utf-8"))
                except OSError:
                    pass

    def _handle(self, request) -> dict:
        if not self.enabled or not isinstance(request, dict):
            raise RuntimeError("Modo robot no autorizado o solicitud inválida")
        kind = request.get("type")
        if kind == "arm":
            if not self.executor.claim("face_follow"):
                raise RuntimeError("Otro controlador está usando los servos")
            try:
                self.executor.activate()
                self._follow_active = True
                self._position = 0.0
                self._last_update = time.monotonic()
                return {"ok": True}
            except Exception:
                self.executor.release("face_follow")
                raise
        if kind == "stop":
            if not self._follow_active:
                return {"ok": True}
            self._follow_active = False
            self.executor.stop()
            return {"ok": True}
        if kind == "velocity":
            velocity, sent_at = request.get("value"), request.get("time")
            if (not self._follow_active or isinstance(velocity, bool) or
                    not isinstance(velocity, (int, float)) or not math.isfinite(velocity) or
                    not isinstance(sent_at, (int, float)) or not math.isfinite(sent_at) or
                    abs(time.monotonic() - sent_at) > 0.35):
                raise RuntimeError("Objetivo facial vencido o seguimiento desarmado")
            now = time.monotonic()
            dt = min(0.15, max(0.0, now - self._last_update))
            self._last_update = now
            bounded_velocity = max(-0.5, min(0.5, float(velocity)))
            self._position = max(-0.15, min(0.15, self._position + bounded_velocity * dt))
            self.executor.set_axis_target("HEAD_PAN", round(self._position * 1000), owner="face_follow")
            return {"ok": True, "position": self._position}
        raise ValueError("Operación IPC desconocida")

    def stop(self) -> None:
        self._stop.set()
        listener, self._socket = self._socket, None
        if listener is not None:
            listener.close()
        worker, self._thread = self._thread, None
        if worker is not None:
            worker.join(timeout=0.6)
        try:
            if self.path.is_socket():
                self.path.unlink()
        except OSError:
            pass


class MotionIpcClient:
    def __init__(self, path: str | Path | None = None, timeout: float = 0.15) -> None:
        self.path = Path(path) if path is not None else motion_socket_path()
        self.timeout = timeout

    def request(self, kind: str, **values) -> dict:
        payload = json.dumps({"type": kind, **values}, separators=(",", ":")).encode("utf-8")
        if len(payload) > 512:
            raise ValueError("Mensaje IPC demasiado grande")
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(self.timeout)
            client.connect(str(self.path))
            client.sendall(payload)
            response = json.loads(client.recv(513).decode("utf-8"))
        if not isinstance(response, dict) or response.get("ok") is not True:
            raise RuntimeError(response.get("error", "Movimiento IPC rechazado"))
        return response


class IpcHeadAdapter:
    """Adaptador de velocidad normalizada; no abre UART en el proceso de cámara."""

    is_physical = True

    def __init__(self, client: MotionIpcClient | None = None) -> None:
        self.client = client or MotionIpcClient()
        self.is_armed = False

    def arm(self) -> bool:
        try:
            self.client.request("arm")
            self.is_armed = True
            return True
        except (OSError, RuntimeError, ValueError):
            self.is_armed = False
            return False

    def set_pan_velocity(self, velocity: float) -> None:
        if not self.is_armed:
            raise RuntimeError("Seguimiento físico no armado")
        self.client.request("velocity", value=float(velocity), time=time.monotonic())

    def stop(self) -> None:
        self.is_armed = False
        try:
            self.client.request("stop")
        except (OSError, RuntimeError, ValueError):
            pass
