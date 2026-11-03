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
