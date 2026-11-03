"""Camera -> face detector -> smoothed, normalized look target.

``FaceTarget(x, y, confidence)`` uses 0..1 coordinates in *screen* space:
(0.5, 0.5) is straight ahead, x=0 means "look toward the screen's left".
Because the camera faces the person, its image is mirrored relative to the
screen; ``mirror=True`` (the default) undoes that so the eyes look at you.

Environment:
    CUTY_CAMERA_MIRROR  1 (default) or 0 if the eyes move the wrong way
    CUTY_TRACK_FPS      detection rate, default 12
"""

from __future__ import annotations

import logging
import math
import os
import threading
import time
from dataclasses import dataclass
from typing import Callable

from cuty.vision.camera import Camera, CameraError, open_camera
from cuty.vision.face_detector import Detection, DetectorError, create_detector


@dataclass(frozen=True)
class FaceTarget:
    x: float
    y: float
    confidence: float
    timestamp: float


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class FaceTracker:
    """Keeps the most recent target; safe to read from the render thread."""

    def __init__(self, camera_factory: Callable[[], Camera] = open_camera,
                 detector_factory: Callable[[], object] = create_detector,
                 *, mirror: bool | None = None, fps: float | None = None,
                 lost_after: float = 0.8, smoothing: float = 0.45,
                 retry_after: float = 5.0, clock: Callable[[], float] = time.monotonic) -> None:
        self._camera_factory = camera_factory
        self._detector_factory = detector_factory
        self.mirror = _env_flag("CUTY_CAMERA_MIRROR", True) if mirror is None else mirror
        self.fps = fps if fps is not None else float(os.getenv("CUTY_TRACK_FPS", "12") or 12)
        self.lost_after = lost_after
        self.smoothing = smoothing
        self.retry_after = retry_after
        self._clock = clock
        self._lock = threading.Lock()
        self._target: FaceTarget | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.status = "detenido"
        self._log = logging.getLogger("VISION")

    # ----- pure tracking logic (no camera), easy to test --------------------
    def _point(self, d: Detection, frame_w: int, frame_h: int) -> tuple[float, float]:
        """Where to look, normalized and mirrored: the eyes if known."""
        if d.eyes_x is not None and d.eyes_y is not None:
            x, y = d.eyes_x / frame_w, d.eyes_y / frame_h
        else:
            x, y = (d.x + d.w / 2) / frame_w, (d.y + d.h * 0.4) / frame_h
        return (1.0 - x if self.mirror else x), y

    def process(self, detections: list, frame_w: int, frame_h: int, now: float) -> FaceTarget | None:
        boxes = [d if isinstance(d, Detection) else Detection(*d) for d in detections]
        with self._lock:
            previous = self._target
        if not boxes:
            if previous is not None and now - previous.timestamp > self.lost_after:
                previous = None
            with self._lock:
                self._target = previous
            return previous
        best = self._choose(boxes, frame_w, frame_h, previous)
        nx, ny = self._point(best, frame_w, frame_h)
        confidence = max(0.0, min(1.0, best.score))
        if previous is not None and now - previous.timestamp <= self.lost_after:
            k = self.smoothing
            nx = previous.x + (nx - previous.x) * (1 - k)
            ny = previous.y + (ny - previous.y) * (1 - k)
        target = FaceTarget(min(1.0, max(0.0, nx)), min(1.0, max(0.0, ny)), confidence, now)
        with self._lock:
            self._target = target
        return target

    def _choose(self, boxes: list[Detection], frame_w, frame_h, previous) -> Detection:
        """Prefer big (close) faces, but stick with whoever we were already watching."""
        def score(d: Detection) -> float:
            s = d.w * d.h
            if previous is not None:
                cx, cy = self._point(d, frame_w, frame_h)
                s *= 1.0 / (1.0 + 4.0 * math.hypot(cx - previous.x, cy - previous.y))
            return s
        return max(boxes, key=score)

    def latest(self) -> FaceTarget | None:
        with self._lock:
            target = self._target
        if target is not None and self._clock() - target.timestamp > self.lost_after:
            return None
        return target

    # ----- background thread ----------------------------------------------
    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="cuty-vision")
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout)
            self._thread = None
        with self._lock:
            self._target = None
        self.status = "detenido"

    def _run(self) -> None:
        try:
            detector = self._detector_factory()
        except DetectorError as exc:
            self.status = f"sin detector: {exc}"
            self._log.warning("Seguimiento de caras desactivado: %s", exc)
            return
        period = 1.0 / max(1.0, self.fps)
        while not self._stop.is_set():
            try:
                camera = self._camera_factory()
            except CameraError as exc:
                self.status = f"sin cámara: {exc}"
                self._log.warning("%s (reintento en %.0f s)", exc, self.retry_after)
                if self._stop.wait(self.retry_after):
                    return
                continue
            self.status = "siguiendo"
            self._log.info("Cámara lista; los ojos siguen a las personas")
            seen = False
            try:
                while not self._stop.is_set():
                    started = self._clock()
                    gray = camera.read_gray()
                    target = self.process(detector.detect(gray), gray.shape[1], gray.shape[0], self._clock())
                    if (target is not None) != seen:
                        seen = target is not None
                        self._log.info("Persona %s", "detectada" if seen else "perdida")
                    self._stop.wait(max(0.0, period - (self._clock() - started)))
            except CameraError as exc:
                self.status = f"cámara perdida: {exc}"
                self._log.warning("%s", exc)
            except Exception:
                self.status = "error de visión"
                self._log.exception("Error en el seguimiento de caras")
            finally:
                try:
                    camera.close()
                except Exception:
                    pass
            if self._stop.wait(1.0):
                return
