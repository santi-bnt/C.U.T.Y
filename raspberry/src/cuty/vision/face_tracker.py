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

from cuty.vision.camera import FRAME_SIZE, Camera, CameraError, open_camera
from cuty.vision.face_detector import Detection, DetectorError, create_detector
from cuty.vision.head_follow import (
    FaceFollowConfig,
    FaceFollowController,
    FollowConfigurationError,
    FollowStatus,
)


@dataclass(frozen=True)
class FaceTarget:
    x: float
    y: float
    confidence: float
    timestamp: float


@dataclass(frozen=True)
class FaceObservation:
    generation: int
    timestamp: float
    color_bgr: object
    detections: tuple[Detection, ...]
    detection_size: tuple[int, int] | None = None


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
                 retry_after: float = 5.0, clock: Callable[[], float] = time.monotonic,
                 vision_ipc_path: str | os.PathLike | None = None,
                 vision_user: str = "santi") -> None:
        self._camera_factory = camera_factory
        self._detector_factory = detector_factory
        self.mirror = _env_flag("CUTY_CAMERA_MIRROR", True) if mirror is None else mirror
        self.fps = fps if fps is not None else float(os.getenv("CUTY_TRACK_FPS", "12") or 12)
        self.lost_after = lost_after
        self.smoothing = smoothing
        self.retry_after = retry_after
        self._clock = clock
        self._lock = threading.Lock()
        self._frame_condition = threading.Condition()
        self._frame_generation = 0
        self._observation: FaceObservation | None = None
        self._color_requested = threading.Event()
        self._vision_ipc_path = vision_ipc_path
        self._vision_user = vision_user
        self._vision_server = None
        self._target: FaceTarget | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.status = "detenido"
        self._log = logging.getLogger("VISION")
        self.follow: FaceFollowController | None = None
        self._last_follow_log = 0.0
        try:
            follow_config = FaceFollowConfig.from_env()
            if follow_config.enabled:
                self._log.warning(
                    "Seguimiento de cabeza habilitado solo en dry-run; "
                    "no hay protocolo ni actuador STM32 verificado"
                )
            if follow_config.dry_run:
                # Keep an inert controller available for an internal runtime
                # toggle; it performs no work or I/O while disabled.
                self.follow = FaceFollowController(follow_config, clock=clock)
        except FollowConfigurationError as exc:
            self.status = f"seguimiento de cabeza bloqueado: {exc}"
            self._log.error("%s", self.status)

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
            self._update_follow(previous, now)
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
        self._update_follow(target, now)
        return target

    def _update_follow(self, target: FaceTarget | None, now: float) -> None:
        if self.follow is None:
            return
        state = self.follow.update(target, now)
        if now - self._last_follow_log >= 1.0:
            self._last_follow_log = now
            self._log.info(
                "[HEAD FOLLOW DRY-RUN] active=%s track=%s err=(%+.3f,%+.3f) "
                "pid_pan=%+.3f sim_velocity=%+.3f sim_position=%+.3f (%s)",
                state.enabled, state.tracking,
                state.x_error if state.x_error is not None else 0.0,
                state.y_error if state.y_error is not None else 0.0,
                state.pid_output, state.velocity, state.simulated_position, state.reason,
            )

    def set_head_follow_enabled(self, enabled: bool) -> bool:
        """Internal toggle for simulation; no physical servo path exists."""
        if self.follow is None:
            return False
        self.follow.set_enabled(enabled)
        self._log.info("Seguimiento facial %s (solo simulación)", "activado" if enabled else "detenido")
        return True

    @property
    def head_follow_status(self) -> FollowStatus | None:
        return self.follow.status if self.follow is not None else None

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

    def capture_observation(self, *, after_generation: int | None = None,
                            timeout: float = 2.0) -> FaceObservation:
        """Request one color frame from the existing camera loop and wait for it."""
        with self._frame_condition:
            baseline = self._frame_generation if after_generation is None else after_generation
            self._color_requested.set()
            ready = self._frame_condition.wait_for(
                lambda: self._observation is not None and self._observation.generation > baseline,
                timeout=max(0.0, timeout),
            )
            if not ready or self._observation is None:
                raise TimeoutError("No se recibió un fotograma de color reciente de FaceTracker")
            observation = self._observation
            self._observation = None
            image = observation.color_bgr
            copy = getattr(image, "copy", None)
            return FaceObservation(
                observation.generation, observation.timestamp,
                copy() if callable(copy) else image, observation.detections, FRAME_SIZE,
            )

    def _publish_observation(self, color_bgr, detections: list[Detection], now: float) -> None:
        with self._frame_condition:
            self._frame_generation += 1
            if color_bgr is not None:
                self._observation = FaceObservation(
                    self._frame_generation, now, color_bgr, tuple(detections),
                )
                self._color_requested.clear()
            self._frame_condition.notify_all()

    # ----- background thread ----------------------------------------------
    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        if self.follow is not None and self.follow.config.enabled:
            self.follow.set_enabled(True)
        if self._vision_ipc_path is not None and self._vision_server is None:
            try:
                import pwd
                from cuty.vision.ipc import FaceTrackerVisionService, LocalVisionServer
                uid = pwd.getpwnam(self._vision_user).pw_uid
                service = FaceTrackerVisionService(self)
                self._vision_server = LocalVisionServer(
                    self._vision_ipc_path, service.handle, allowed_uid=uid,
                )
                self._vision_server.start()
            except Exception as exc:
                self._vision_server = None
                self._log.error("IPC local de visión desactivado: %s", exc)
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="cuty-vision")
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        self._stop.set()
        if self._vision_server is not None:
            self._vision_server.stop()
            self._vision_server = None
        if self._thread is not None:
            self._thread.join(timeout)
            self._thread = None
        with self._lock:
            self._target = None
        with self._frame_condition:
            self._observation = None
            self._color_requested.clear()
            self._frame_condition.notify_all()
        if self.follow is not None:
            self.follow.set_enabled(False)
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
            metric_started = self._clock()
            metric_frames = 0
            capture_total = detect_total = frame_to_pan_total = 0.0
            try:
                while not self._stop.is_set():
                    started = self._clock()
                    read_frame = getattr(camera, "read_frame", None)
                    if callable(read_frame):
                        frame = read_frame(include_color=self._color_requested.is_set())
                        gray, color_bgr = frame.gray, frame.color_bgr
                        captured_at = frame.captured_at or self._clock()
                    else:
                        gray, color_bgr = camera.read_gray(), None
                        captured_at = self._clock()
                    capture_finished = self._clock()
                    capture_total += capture_finished - started
                    detect_started = capture_finished
                    detections = detector.detect(gray)
                    now = self._clock()
                    detect_total += now - detect_started
                    self._publish_observation(color_bgr, detections, now)
                    target = self.process(detections, gray.shape[1], gray.shape[0], now)
                    pan_completed = self._clock()
                    frame_to_pan_total += max(0.0, pan_completed - captured_at)
                    metric_frames += 1
                    if (target is not None) != seen:
                        seen = target is not None
                        self._log.info("Persona %s", "detectada" if seen else "perdida")
                    elapsed = now - metric_started
                    if elapsed >= 5.0:
                        self._log.info(
                            "[VISION PERF] fps=%.2f capture_ms=%.1f detect_ms=%.1f frame_to_pan_ms=%.1f frames=%d",
                            metric_frames / elapsed,
                            capture_total * 1000 / max(1, metric_frames),
                            detect_total * 1000 / max(1, metric_frames),
                            frame_to_pan_total * 1000 / max(1, metric_frames), metric_frames,
                        )
                        metric_started = now
                        metric_frames = 0
                        capture_total = detect_total = frame_to_pan_total = 0.0
                    self._stop.wait(max(0.0, period - (self._clock() - started)))
            except CameraError as exc:
                self.status = f"cámara perdida: {exc}"
                self._log.warning("%s", exc)
            except Exception:
                self.status = "error de visión"
                self._log.exception("Error en el seguimiento de caras")
            finally:
                if self.follow is not None:
                    self.follow.update(None, self._clock())
                try:
                    camera.close()
                except Exception:
                    pass
            if self._stop.wait(1.0):
                return
