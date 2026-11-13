"""Camera capture returning small grayscale frames for face detection.

Supports the Raspberry Pi camera (Picamera2/libcamera) and USB webcams
(OpenCV). Both are optional imports so the rest of C.U.T.Y runs without them.

Environment:
    CUTY_CAMERA         auto (default) | picamera | usb | off
    CUTY_CAMERA_INDEX   USB camera index, default 0
    CUTY_CAMERA_ROTATE  0 (default), 90, 180 or 270 degrees clockwise
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Protocol

import numpy as np

FRAME_SIZE = (320, 240)


class CameraError(RuntimeError):
    pass


@dataclass(frozen=True)
class CameraFrame:
    gray: np.ndarray
    # OpenCV BGR order; populated only on an explicit, user-requested snapshot.
    color_bgr: np.ndarray | None = None
    # Monotonic time when the completed capture became available to Python.
    # This is useful for capture-to-controller latency; it is not the sensor
    # exposure timestamp (libcamera's internal queue age is not included).
    captured_at: float | None = None


class Camera(Protocol):
    def read_gray(self) -> np.ndarray: ...
    def read_frame(self, *, include_color: bool = False) -> CameraFrame: ...
    def close(self) -> None: ...


def _rotate(gray: np.ndarray, degrees: int) -> np.ndarray:
    turns = (degrees // 90) % 4
    # np.rot90 is counter-clockwise; negate for clockwise rotation.
    return np.ascontiguousarray(np.rot90(gray, -turns)) if turns else gray


class PiCamera:
    def __init__(self, rotate: int = 0, high_res_snapshot: bool | None = None) -> None:
        try:
            from picamera2 import Picamera2
        except ImportError as exc:
            raise CameraError("picamera2 no está instalado (sudo apt install python3-picamera2)") from exc
        self.rotate = rotate
        self.high_res_snapshot = (
            os.getenv("CUTY_CAMERA_HIGH_RES_SNAPSHOT", "0").strip().lower() in {"1", "true", "yes", "on"}
            if high_res_snapshot is None else high_res_snapshot
        )
        self._main_size = FRAME_SIZE
        try:
            self._cam = Picamera2()
            # Default stays identical. The opt-in configuration keeps a QVGA
            # lores stream for tracking and a moderate 4:3 main stream for
            # explicitly requested snapshots, all from the same camera.
            if self.high_res_snapshot:
                config = self._cam.create_video_configuration(
                    main={"size": (1296, 972), "format": "YUV420"},
                    lores={"size": FRAME_SIZE, "format": "YUV420"}, buffer_count=2)
            else:
                config = self._cam.create_video_configuration(
                    main={"size": FRAME_SIZE, "format": "YUV420"}, buffer_count=2)
            self._cam.configure(config)
            if self.high_res_snapshot:
                self._main_size = tuple(self._cam.stream_configuration("main")["size"])
                logging.getLogger("VISION").info(
                    "Cámara dual stream activa: main=%sx%s, lores=%sx%s; validar carga en Pi",
                    *self._main_size, *FRAME_SIZE,
                )
            self._cam.start()
        except Exception as exc:  # libcamera raises many types
            raise CameraError(f"No se pudo abrir la cámara de la Raspberry: {exc}") from exc

    def read_gray(self) -> np.ndarray:
        return self.read_frame().gray

    def read_frame(self, *, include_color: bool = False) -> CameraFrame:
        if self.high_res_snapshot:
            if include_color:
                (frame, low_frame), _metadata = self._cam.capture_arrays(["main", "lores"])
            else:
                low_frame = self._cam.capture_array("lores")
                frame = None
            gray = _rotate(low_frame[: FRAME_SIZE[1], : FRAME_SIZE[0]], self.rotate)
        else:
            frame = self._cam.capture_array("main")
            gray = _rotate(frame[: FRAME_SIZE[1], : FRAME_SIZE[0]], self.rotate)
        color = None
        if include_color:
            try:
                import cv2
                color = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_I420)
            except Exception as exc:
                raise CameraError(f"No se pudo convertir el fotograma para visión: {exc}") from exc
            color = color[:self._main_size[1], :self._main_size[0]]
            color = _rotate(color, self.rotate)
        return CameraFrame(gray=gray, color_bgr=color, captured_at=time.monotonic())

    def close(self) -> None:
        try:
            self._cam.stop()
        finally:
            self._cam.close()


class UsbCamera:
    def __init__(self, index: int = 0, rotate: int = 0) -> None:
        try:
            import cv2
        except ImportError as exc:
            raise CameraError("OpenCV no está instalado (sudo apt install python3-opencv)") from exc
        self._cv2 = cv2
        self.rotate = rotate
        self._cap = cv2.VideoCapture(index)
        if not self._cap.isOpened():
            raise CameraError(f"No se pudo abrir la cámara USB {index}")
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_SIZE[0])
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_SIZE[1])
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # always the newest frame

    def read_gray(self) -> np.ndarray:
        return self.read_frame().gray

    def read_frame(self, *, include_color: bool = False) -> CameraFrame:
        ok, frame = self._cap.read()
        if not ok or frame is None:
            raise CameraError("La cámara USB dejó de enviar imágenes")
        if frame.shape[1] != FRAME_SIZE[0] or frame.shape[0] != FRAME_SIZE[1]:
            frame = self._cv2.resize(frame, FRAME_SIZE, interpolation=self._cv2.INTER_AREA)
        gray = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2GRAY)
        color = _rotate(frame, self.rotate) if include_color else None
        return CameraFrame(gray=_rotate(gray, self.rotate), color_bgr=color, captured_at=time.monotonic())

    def close(self) -> None:
        self._cap.release()


def camera_mode() -> str:
    mode = os.getenv("CUTY_CAMERA", "auto").strip().lower()
    return mode if mode in {"auto", "picamera", "usb", "off"} else "auto"


def open_camera() -> Camera:
    """Open the configured camera; ``auto`` tries the Pi camera, then USB."""
    mode = camera_mode()
    rotate = int(os.getenv("CUTY_CAMERA_ROTATE", "0") or 0)
    if rotate not in (0, 90, 180, 270):
        raise CameraError("CUTY_CAMERA_ROTATE debe ser 0, 90, 180 o 270")
    index = int(os.getenv("CUTY_CAMERA_INDEX", "0") or 0)
    if mode == "off":
        raise CameraError("Cámara desactivada (CUTY_CAMERA=off)")
    if mode == "picamera":
        return PiCamera(rotate)
    if mode == "usb":
        return UsbCamera(index, rotate)
    errors = []
    # High-resolution snapshots are Pi-camera-only and opt-in. Do not silently
    # change to USB if Picamera2 cannot satisfy the requested stream config.
    high_res = os.getenv("CUTY_CAMERA_HIGH_RES_SNAPSHOT", "0").strip().lower() in {"1", "true", "yes", "on"}
    if high_res:
        return PiCamera(rotate, high_res_snapshot=True)
    for factory in (lambda: PiCamera(rotate), lambda: UsbCamera(index, rotate)):
        try:
            return factory()
        except CameraError as exc:
            errors.append(str(exc))
    logging.getLogger("VISION").debug("Cámaras probadas: %s", errors)
    raise CameraError("No se encontró cámara: " + " / ".join(errors))
