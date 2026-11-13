"""Camera face tracking without a camera: fake frames and detections."""

import threading
import time

import numpy as np
import pytest

from cuty.vision.camera import CameraError, _rotate
from cuty.vision.face_detector import Detection, DetectorError
from cuty.vision.face_tracker import FaceTracker


def tracker(**kw):
    return FaceTracker(camera_factory=None, detector_factory=None, smoothing=0.0, **kw)


def test_target_is_mirrored_so_eyes_look_at_the_person():
    # Person on the left of the camera image = the robot's left = screen right.
    t = tracker(mirror=True).process([Detection(20, 100, 60, 60)], 320, 240, 0.0)
    assert t.x > 0.8 and 0.4 < t.y < 0.6
    t = tracker(mirror=False).process([Detection(20, 100, 60, 60)], 320, 240, 0.0)
    assert t.x < 0.2


def test_eye_landmarks_are_preferred_over_the_box():
    t = tracker(mirror=False).process([Detection(0, 0, 320, 240, 0.9, 160, 60)], 320, 240, 0.0)
    assert (t.x, t.y) == (0.5, 0.25) and t.confidence == 0.9


def test_closest_face_wins_and_tracking_sticks():
    tr = tracker(mirror=False)
    small, big = Detection(10, 10, 30, 30), Detection(200, 100, 90, 90)
    first = tr.process([small, big], 320, 240, 0.0)
    assert first.x > 0.6
    # A similar-sized stranger far away does not steal attention.
    near = Detection(205, 100, 85, 85)
    far = Detection(5, 100, 95, 95)
    assert tr.process([far, near], 320, 240, 0.1).x > 0.6


def test_target_survives_brief_misses_then_is_lost():
    clock = [0.0]
    tr = FaceTracker(camera_factory=None, detector_factory=None, lost_after=0.5, clock=lambda: clock[0])
    tr.process([Detection(100, 80, 80, 80)], 320, 240, 0.0)
    clock[0] = 0.3
    assert tr.process([], 320, 240, 0.3) is not None and tr.latest() is not None
    clock[0] = 0.9
    assert tr.process([], 320, 240, 0.9) is None and tr.latest() is None


def test_smoothing_moves_part_of_the_way():
    tr = FaceTracker(camera_factory=None, detector_factory=None, mirror=False, smoothing=0.5)
    tr.process([Detection(0, 100, 40, 40)], 320, 240, 0.0)
    second = tr.process([Detection(280, 100, 40, 40)], 320, 240, 0.05)
    assert 0.4 < second.x < 0.6


def test_head_follow_uses_existing_face_target_and_stops_after_half_second(monkeypatch):
    monkeypatch.setenv("CUTY_FOLLOW_ENABLED", "1")
    monkeypatch.setenv("CUTY_FOLLOW_DRY_RUN", "1")
    monkeypatch.setenv("CUTY_FOLLOW_DETECTION_ALPHA", "1")
    clock = [0.0]
    tr = tracker(mirror=False, lost_after=0.8, clock=lambda: clock[0])
    assert tr.follow is not None
    seen = tr.process([Detection(250, 90, 40, 40)], 320, 240, 0.0)
    assert seen.x > 0.8 and tr.latest() is seen
    tr.process([Detection(250, 90, 40, 40)], 320, 240, 0.1)
    assert tr.head_follow_status.tracking
    # FaceTracker's eye-gaze retention can be longer; head motion has its own
    # 0.5 s loss deadline and receives no new camera or detector instance.
    tr.process([], 320, 240, 0.61)
    clock[0] = 0.61
    assert tr.latest() is not None
    assert not tr.head_follow_status.tracking
    assert tr.head_follow_status.velocity == 0


def test_physical_follow_configuration_is_blocked_without_affecting_tracker(monkeypatch):
    monkeypatch.setenv("CUTY_FOLLOW_ENABLED", "1")
    monkeypatch.setenv("CUTY_FOLLOW_DRY_RUN", "0")
    tr = tracker()
    assert tr.follow is None
    assert "bloqueado" in tr.status


def test_runtime_follow_toggle_is_available_but_inert_by_default(monkeypatch):
    monkeypatch.delenv("CUTY_FOLLOW_ENABLED", raising=False)
    monkeypatch.delenv("CUTY_FOLLOW_DRY_RUN", raising=False)
    tr = tracker()
    assert tr.follow is not None and not tr.head_follow_status.enabled
    assert tr.set_head_follow_enabled(True)
    assert tr.head_follow_status.enabled
    assert tr.set_head_follow_enabled(False)
    assert tr.head_follow_status.reason == "manual stop"


def test_rotation():
    frame = np.arange(6).reshape(2, 3)
    assert _rotate(frame, 0) is frame
    assert _rotate(frame, 90).shape == (3, 2)
    assert (_rotate(frame, 180) == frame[::-1, ::-1]).all()


def test_thread_runs_with_fake_camera_and_stops():
    frames = []

    class FakeCamera:
        def read_gray(self):
            frames.append(1)
            return np.zeros((240, 320), dtype=np.uint8)

        def close(self):
            pass

    class FakeDetector:
        def detect(self, gray):
            return [Detection(140, 100, 40, 40)]

    tr = FaceTracker(FakeCamera, FakeDetector, fps=50)
    tr.start()
    deadline = time.monotonic() + 2
    while tr.latest() is None and time.monotonic() < deadline:
        time.sleep(0.01)
    assert tr.latest() is not None and tr.status == "siguiendo"
    tr.stop()
    assert tr.latest() is None and not any(t.name == "cuty-vision" for t in threading.enumerate())


def test_requested_color_snapshot_reuses_the_single_tracker_camera():
    opened = []
    color_reads = []

    class FakeCamera:
        def __init__(self): opened.append(self)
        def read_frame(self, *, include_color=False):
            if include_color:
                color_reads.append(True)
            gray = np.zeros((240, 320), dtype=np.uint8)
            color = np.full((240, 320, 3), 17, dtype=np.uint8) if include_color else None
            from cuty.vision.camera import CameraFrame
            return CameraFrame(gray, color)
        def close(self): pass

    class FakeDetector:
        def detect(self, _gray): return []

    tr = FaceTracker(FakeCamera, FakeDetector, fps=40)
    tr.start()
    try:
        observation = tr.capture_observation(timeout=1)
        assert observation.color_bgr.shape == (240, 320, 3)
        assert len(opened) == 1
        assert len(color_reads) == 1
    finally:
        tr.stop()


def test_missing_camera_or_detector_is_not_fatal():
    def no_camera():
        raise CameraError("sin cámara")

    def no_detector():
        raise DetectorError("sin OpenCV")

    tr = FaceTracker(no_camera, lambda: object(), retry_after=0.05)
    tr.start()
    time.sleep(0.15)
    assert tr.status.startswith("sin cámara")
    tr.stop()
    tr = FaceTracker(no_camera, no_detector)
    tr.start()
    time.sleep(0.1)
    assert tr.status.startswith("sin detector")
    tr.stop()


def test_real_detector_loads_when_opencv_is_installed():
    pytest.importorskip("cv2")
    from cuty.vision.face_detector import create_detector

    detector = create_detector()
    assert detector.detect(np.zeros((240, 320), dtype=np.uint8)) == []
