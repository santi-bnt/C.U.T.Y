"""Private Unix-domain IPC between touchscreen FaceTracker and voice process."""

from __future__ import annotations

import base64
import json
import logging
import os
import socket
import struct
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from cuty.vision.recognition import LocalFaceRecognition

MAX_MESSAGE = 1_500_000


def socket_path_for_user(user: str = "santi") -> Path:
    try:
        import pwd
        uid = pwd.getpwnam(user).pw_uid
    except (ImportError, KeyError):
        uid = os.getuid() if hasattr(os, "getuid") else 0
    return Path(os.getenv("CUTY_VISION_SOCKET", f"/run/cuty-vision-{uid}.sock"))


def _recv_exact(connection: socket.socket, size: int) -> bytes:
    result = bytearray()
    while len(result) < size:
        chunk = connection.recv(size - len(result))
        if not chunk:
            raise ConnectionError("IPC connection closed early")
        result.extend(chunk)
    return bytes(result)


def _read_message(connection: socket.socket) -> dict:
    size = struct.unpack("!I", _recv_exact(connection, 4))[0]
    if size <= 0 or size > 4096:
        raise ValueError("Invalid IPC request size")
    message = json.loads(_recv_exact(connection, size).decode("utf-8"))
    if not isinstance(message, dict):
        raise ValueError("Invalid IPC request")
    return message


def _send_message(connection: socket.socket, message: dict) -> None:
    payload = json.dumps(message, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(payload) > MAX_MESSAGE:
        raise ValueError("IPC response is too large")
    connection.sendall(struct.pack("!I", len(payload)) + payload)


class FaceTrackerVisionService:
    """Operations over a FaceTracker instance; never captures a second camera."""

    def __init__(self, tracker, recognition: LocalFaceRecognition | None = None,
                 *, enrollment_samples: int | None = None, sample_gap: float = 0.25) -> None:
        self.tracker = tracker
        self.recognition = recognition
        self.enrollment_samples = int(enrollment_samples or os.getenv("CUTY_FACE_ENROLL_SAMPLES", "5"))
        self.sample_gap = sample_gap
        if not 3 <= self.enrollment_samples <= 8:
            raise ValueError("CUTY_FACE_ENROLL_SAMPLES must be from 3 to 8")

    def handle(self, request: dict) -> dict:
        action = request.get("action")
        if action == "capture":
            from cuty.vision.recognition import mask_faces_and_encode
            started = time.monotonic()
            observation = self.tracker.capture_observation(timeout=3.0)
            captured = time.monotonic()
            image = mask_faces_and_encode(observation)
            logging.getLogger("VISION").info(
                "[VISION PERF] ipc_capture_wait_ms=%.1f total_capture_prepare_ms=%.1f",
                (captured - started) * 1000, (time.monotonic() - started) * 1000,
            )
            return {"ok": True, "jpeg": base64.b64encode(image).decode("ascii")}
        if action == "identify":
            recognition = self._recognition()
            observation = self.tracker.capture_observation(timeout=3.0)
            return {"ok": True, **recognition.identify(observation)}
        if action == "enroll":
            recognition = self._recognition()
            name = request.get("name")
            if not isinstance(name, str):
                raise ValueError("A consented display name is required")
            observations = []
            generation = None
            for index in range(self.enrollment_samples):
                if index:
                    time.sleep(self.sample_gap)
                observation = self.tracker.capture_observation(
                    after_generation=generation, timeout=3.0,
                )
                observations.append(observation)
                generation = observation.generation
            saved_name = recognition.enroll(name, observations)
            return {"ok": True, "name": saved_name, "samples": len(observations)}
        if action == "forget":
            recognition = self._recognition()
            observation = self.tracker.capture_observation(timeout=3.0)
            identity = recognition.identify(observation)
            if not identity.get("known") or not identity.get("name"):
                return {"ok": True, "deleted": False, "matched": False}
            deleted = recognition.forget(str(identity["name"]))
            return {"ok": True, "deleted": deleted, "matched": True}
        raise ValueError("Unknown local vision operation")

    def _recognition(self):
        if self.recognition is None:
            from cuty.vision.recognition import LocalFaceRecognition
            self.recognition = LocalFaceRecognition()
        return self.recognition


class LocalVisionServer:
    """Restricted local IPC listener; not an HTTP endpoint and not LAN accessible."""

    def __init__(self, path: str | Path, handler: Callable[[dict], dict], allowed_uid: int) -> None:
        if not hasattr(socket, "AF_UNIX"):
            raise OSError("Unix-domain sockets are unavailable")
        self.path = Path(path)
        self.handler = handler
        self.allowed_uid = int(allowed_uid)
        self._stop = threading.Event()
        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists() or self.path.is_symlink():
            if not self.path.is_socket():
                raise OSError(f"Refusing to replace a non-socket path: {self.path}")
            self.path.unlink()
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            listener.bind(str(self.path))
            os.chmod(self.path, 0o600)
            if hasattr(os, "geteuid") and os.geteuid() == 0:
                os.chown(self.path, self.allowed_uid, -1)
            listener.listen(2)
            listener.settimeout(0.25)
            self._socket = listener
            self._thread = threading.Thread(target=self._serve, daemon=True, name="cuty-vision-ipc")
            self._thread.start()
        except Exception:
            listener.close()
            if self.path.exists() and self.path.is_socket():
                self.path.unlink()
            raise

    def _authorized(self, connection: socket.socket) -> bool:
        if not hasattr(socket, "SO_PEERCRED"):
            # The socket file itself is mode 0600 and owned by the client UID.
            return True
        try:
            _, uid, _ = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
            return uid == self.allowed_uid
        except OSError:
            return False

    def _serve(self) -> None:
        listener = self._socket
        while not self._stop.is_set() and listener is not None:
            try:
                connection, _ = listener.accept()
            except (TimeoutError, socket.timeout):
                continue
            except OSError:
                break
            with connection:
                connection.settimeout(18.0)
                if not self._authorized(connection):
                    try:
                        _send_message(connection, {"ok": False, "error": "Acceso local denegado"})
                    except OSError:
                        pass
                    continue
                try:
                    request = _read_message(connection)
                    response = self.handler(request)
                except (ValueError, TimeoutError) as exc:
                    response = {"ok": False, "error": str(exc)[:240]}
                except Exception:
                    response = {"ok": False, "error": "Falló una operación local de visión"}
                try:
                    _send_message(connection, response)
                except (OSError, ValueError):
                    pass

    def stop(self, timeout: float = 3.0) -> None:
        self._stop.set()
        listener, self._socket = self._socket, None
        if listener is not None:
            listener.close()
        thread, self._thread = self._thread, None
        if thread is not None:
            thread.join(timeout)
        try:
            if self.path.is_socket():
                self.path.unlink()
        except OSError:
            pass


class LocalVisionClient:
    def __init__(self, path: str | Path, *, timeout: float = 18.0) -> None:
        self.path = Path(path)
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> "LocalVisionClient | None":
        path = os.getenv("CUTY_VISION_SOCKET")
        if not path or os.name != "posix":
            return None
        return cls(path)

    def _request(self, action: str, **data) -> dict:
        request = json.dumps({"action": action, **data}, separators=(",", ":")).encode("utf-8")
        if len(request) > 4096:
            raise ValueError("Local vision request too large")
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(self.timeout)
            connection.connect(str(self.path))
            connection.sendall(struct.pack("!I", len(request)) + request)
            size = struct.unpack("!I", _recv_exact(connection, 4))[0]
            if size <= 0 or size > MAX_MESSAGE:
                raise ValueError("Invalid local vision response size")
            response = json.loads(_recv_exact(connection, size).decode("utf-8"))
        if not response.get("ok"):
            from cuty.vision.recognition import RecognitionUnavailable
            raise RecognitionUnavailable(response.get("error", "Local vision unavailable"))
        return response

    def capture_redacted_jpeg(self) -> bytes:
        started = time.monotonic()
        response = self._request("capture")
        try:
            image = base64.b64decode(response["jpeg"], validate=True)
        except (KeyError, ValueError) as exc:
            from cuty.vision.recognition import RecognitionUnavailable
            raise RecognitionUnavailable("No se recibió una imagen privada válida") from exc
        if not image or len(image) > MAX_MESSAGE:
            from cuty.vision.recognition import RecognitionUnavailable
            raise RecognitionUnavailable("Imagen de visión inválida o demasiado grande")
        logging.getLogger("VISION").info(
            "[VISION PERF] ipc_roundtrip_decode_ms=%.1f jpeg_bytes=%d",
            (time.monotonic() - started) * 1000, len(image),
        )
        return image

    def identify(self) -> dict:
        return self._request("identify")

    def enroll(self, name: str) -> dict:
        return self._request("enroll", name=name)

    def forget(self) -> dict:
        return self._request("forget")
