"""Face detection on small grayscale frames.

Two OpenCV back ends, best first:

* **YuNet** (``cv2.FaceDetectorYN``): a tiny CNN shipped in ``models/``
  (MIT licence, 230 kB). Robust to angles and lighting, a few milliseconds
  per 320x240 frame on a Raspberry Pi 5, and it reports where the eyes are.
* **Haar cascade**: fallback for old OpenCV builds. Pip wheels for OpenCV 4
  ship it under ``cv2.data``; Debian's ``python3-opencv`` in /usr/share/opencv4.

Environment:
    CUTY_FACE_DETECTOR  auto (default) | yunet | haar
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import NamedTuple

import numpy as np

YUNET_MODEL = Path(__file__).resolve().parent / "models" / "face_detection_yunet_2023mar.onnx"
CASCADE = "haarcascade_frontalface_default.xml"
_SEARCH = (
    "/usr/share/opencv4/haarcascades",
    "/usr/share/opencv/haarcascades",
    "/usr/local/share/opencv4/haarcascades",
)


class Detection(NamedTuple):
    x: int
    y: int
    w: int
    h: int
    score: float = 1.0
    eyes_x: float | None = None   # midpoint between the eyes, if known
    eyes_y: float | None = None
    landmarks: tuple[float, ...] | None = None  # YuNet points for local SFace alignment


class DetectorError(RuntimeError):
    pass


def _cv2():
    try:
        import cv2
    except ImportError as exc:
        raise DetectorError("OpenCV no está instalado (sudo apt install python3-opencv)") from exc
    return cv2


def find_cascade(cv2) -> Path:
    folders = []
    data = getattr(cv2, "data", None)
    if data is not None and getattr(data, "haarcascades", None):
        folders.append(data.haarcascades)
    folders.extend(_SEARCH)
    for folder in folders:
        path = Path(folder) / CASCADE
        if path.is_file():
            return path
    raise DetectorError(f"No se encontró {CASCADE}")


class YuNetFaceDetector:
    def __init__(self, score_threshold: float = 0.75, model: Path = YUNET_MODEL) -> None:
        cv2 = _cv2()
        if not hasattr(cv2, "FaceDetectorYN"):
            raise DetectorError("Esta versión de OpenCV no incluye FaceDetectorYN (necesita 4.5.4+)")
        if not Path(model).is_file():
            raise DetectorError(f"Falta el modelo {model}")
        self._cv2 = cv2
        try:
            self._net = cv2.FaceDetectorYN.create(str(model), "", (320, 240), score_threshold, 0.3, 20)
            self._size: tuple[int, int] | None = None
            # The 2023 model needs OpenCV 4.8+; older builds fail here, not mid-tracking.
            self.detect(np.zeros((240, 320), dtype=np.uint8))
        except cv2.error as exc:
            raise DetectorError(f"YuNet no funciona con OpenCV {cv2.__version__}: {exc}") from exc

    def detect(self, gray: np.ndarray) -> list[Detection]:
        h, w = gray.shape[:2]
        if self._size != (w, h):
            self._net.setInputSize((w, h))
            self._size = (w, h)
        image = self._cv2.cvtColor(gray, self._cv2.COLOR_GRAY2BGR) if gray.ndim == 2 else gray
        _, faces = self._net.detect(image)
        if faces is None:
            return []
        found = []
        for row in faces:
            x, y, fw, fh = (int(round(v)) for v in row[:4])
            # Landmarks: right eye (4,5), left eye (6,7) in image coordinates.
            found.append(Detection(
                x, y, fw, fh, float(row[14]),
                float(row[4] + row[6]) / 2, float(row[5] + row[7]) / 2,
                tuple(float(v) for v in row[4:14]),
            ))
        return found


class HaarFaceDetector:
    def __init__(self, min_size: int = 36) -> None:
        cv2 = _cv2()
        if not hasattr(cv2, "CascadeClassifier"):
            raise DetectorError("Esta versión de OpenCV no incluye CascadeClassifier")
        self._cv2 = cv2
        self._cascade = cv2.CascadeClassifier(str(find_cascade(cv2)))
        if self._cascade.empty():
            raise DetectorError("No se pudo cargar el clasificador de caras")
        self.min_size = min_size

    def detect(self, gray: np.ndarray) -> list[Detection]:
        gray = self._cv2.equalizeHist(gray)
        faces = self._cascade.detectMultiScale(
            gray, scaleFactor=1.15, minNeighbors=5,
            minSize=(self.min_size, self.min_size))
        return [Detection(*(int(v) for v in face)) for face in faces]


def create_detector():
    """YuNet when available, otherwise the Haar cascade."""
    choice = os.getenv("CUTY_FACE_DETECTOR", "auto").strip().lower()
    if choice == "yunet":
        return YuNetFaceDetector()
    if choice == "haar":
        return HaarFaceDetector()
    errors = []
    for factory in (YuNetFaceDetector, HaarFaceDetector):
        try:
            return factory()
        except DetectorError as exc:
            errors.append(str(exc))
    raise DetectorError("; ".join(errors))
