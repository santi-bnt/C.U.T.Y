"""On-device SFace embeddings and a permission-restricted face template store.

No image is written to disk. Only embeddings and a user-selected display name
are stored, and enrollment is called only after the voice consent flow confirms.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Protocol, Sequence

import numpy as np

from cuty.vision.face_detector import Detection
from cuty.vision.face_tracker import FaceObservation


class RecognitionUnavailable(RuntimeError):
    pass


class FeatureEngine(Protocol):
    def embed(self, image_bgr: np.ndarray, detection: Detection) -> np.ndarray: ...
    def compare(self, first: np.ndarray, second: np.ndarray) -> float: ...


class OpenCVSFace:
    """OpenCV FaceRecognizerSF wrapper using the locally installed SFace ONNX."""

    def __init__(self, model_path: str | Path) -> None:
        path = Path(model_path).expanduser()
        if not path.is_file():
            raise RecognitionUnavailable(f"Falta el modelo SFace local: {path}")
        try:
            import cv2
            if not hasattr(cv2, "FaceRecognizerSF"):
                raise RecognitionUnavailable("OpenCV no incluye FaceRecognizerSF; instala una compilación compatible")
            self._cv2 = cv2
            self._model = cv2.FaceRecognizerSF.create(str(path), "")
        except RecognitionUnavailable:
            raise
        except Exception as exc:
            raise RecognitionUnavailable(f"No se pudo iniciar SFace: {exc}") from exc

    def embed(self, image_bgr: np.ndarray, detection: Detection) -> np.ndarray:
        if detection.landmarks is None or len(detection.landmarks) != 10:
            raise RecognitionUnavailable("La detección no tiene los 5 puntos YuNet necesarios para alinear el rostro")
        row = np.asarray([[
            detection.x, detection.y, detection.w, detection.h,
            *detection.landmarks, detection.score,
        ]], dtype=np.float32)
        try:
            aligned = self._model.alignCrop(image_bgr, row)
            feature = np.asarray(self._model.feature(aligned), dtype=np.float32).reshape(-1)
        except Exception as exc:
            raise RecognitionUnavailable(f"SFace no pudo extraer una plantilla: {exc}") from exc
        if feature.size < 32 or not np.isfinite(feature).all():
            raise RecognitionUnavailable("SFace devolvió una plantilla inválida")
        return feature

    def compare(self, first: np.ndarray, second: np.ndarray) -> float:
        try:
            return float(self._model.match(
                np.asarray(first, dtype=np.float32).reshape(1, -1),
                np.asarray(second, dtype=np.float32).reshape(1, -1),
                self._cv2.FaceRecognizerSF_FR_COSINE,
            ))
        except Exception as exc:
            raise RecognitionUnavailable(f"No se pudo comparar la plantilla SFace: {exc}") from exc


def _safe_name(name: str) -> str:
    name = " ".join(str(name).strip().split())
    if not 1 <= len(name) <= 40 or any(ord(ch) < 32 for ch in name):
        raise ValueError("El nombre debe tener entre 1 y 40 caracteres")
    return name


def default_store_path() -> Path:
    configured = os.getenv("CUTY_FACE_PROFILE_PATH")
    if configured:
        return Path(configured).expanduser()
    user = os.getenv("CUTY_VISION_USER", "santi")
    try:
        import pwd
        home = Path(pwd.getpwnam(user).pw_dir)
    except (ImportError, KeyError):
        home = Path.home()
    return home / ".local" / "share" / "cuty" / "face_profiles.json"


class FaceProfileStore:
    """Atomic JSON store of embeddings only, kept private to the Pi user."""

    def __init__(self, path: str | Path | None = None, *, owner: str | None = None) -> None:
        self.path = Path(path or default_store_path()).expanduser()
        self.owner = owner or os.getenv("CUTY_VISION_USER", "santi")

    def _owner_ids(self) -> tuple[int, int] | None:
        if os.name != "posix":
            return None
        try:
            import pwd
            entry = pwd.getpwnam(self.owner)
            return entry.pw_uid, entry.pw_gid
        except (ImportError, KeyError):
            return None

    def _secure_directory(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            os.chmod(self.path.parent, 0o700)
            owner = self._owner_ids()
            if owner and os.geteuid() == 0:
                os.chown(self.path.parent, *owner)
        except (AttributeError, OSError):
            pass

    def load(self) -> dict[str, list[np.ndarray]]:
        if self.path.is_symlink():
            raise RecognitionUnavailable("La ruta del archivo facial no puede ser un enlace simbólico")
        if not self.path.exists():
            return {}
        try:
            if self.path.stat().st_size > 256_000:
                raise RecognitionUnavailable("El archivo local de perfiles supera el tamaño permitido")
            document = json.loads(self.path.read_text(encoding="utf-8"))
            if document.get("version") != 1 or not isinstance(document.get("profiles"), dict):
                raise RecognitionUnavailable("Formato de perfiles faciales no reconocido")
            profiles: dict[str, list[np.ndarray]] = {}
            for name, values in document["profiles"].items():
                name = _safe_name(name)
                if not isinstance(values, list) or not 1 <= len(values) <= 8:
                    raise RecognitionUnavailable("Cantidad de plantillas faciales inválida")
                vectors = []
                for value in values:
                    vector = np.asarray(value, dtype=np.float32)
                    if vector.ndim != 1 or not 32 <= vector.size <= 2048 or not np.isfinite(vector).all():
                        raise RecognitionUnavailable("Plantilla facial local inválida")
                    vectors.append(vector)
                profiles[name] = vectors
            return profiles
        except RecognitionUnavailable:
            raise
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise RecognitionUnavailable("No se pudo leer el archivo local de perfiles") from exc

    def save(self, profiles: dict[str, list[np.ndarray]]) -> None:
        self._secure_directory()
        if self.path.is_symlink():
            raise RecognitionUnavailable("La ruta del archivo facial no puede ser un enlace simbólico")
        document = {
            "version": 1,
            "profiles": {name: [vector.astype(float).tolist() for vector in vectors]
                         for name, vectors in profiles.items()},
        }
        fd, temporary = tempfile.mkstemp(prefix=".faces-", suffix=".tmp", dir=self.path.parent)
        try:
            if hasattr(os, "fchmod"):
                os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(document, stream, separators=(",", ":"), ensure_ascii=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            os.chmod(self.path, 0o600)
            owner = self._owner_ids()
            if owner and os.name == "posix" and os.geteuid() == 0:
                os.chown(self.path, *owner)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def forget_all(self) -> bool:
        if self.path.is_symlink():
            raise RecognitionUnavailable("La ruta del archivo facial no puede ser un enlace simbólico")
        if not self.path.exists():
            return False
        self.path.unlink()
        return True

    def forget_profile(self, name: str) -> bool:
        """Delete one explicitly identified profile without touching others."""
        if self.path.is_symlink():
            raise RecognitionUnavailable("La ruta del archivo facial no puede ser un enlace simbólico")
        if not self.path.exists():
            return False
        profiles = self.load()
        if name not in profiles:
            return False
        del profiles[name]
        if profiles:
            self.save(profiles)
        else:
            self.path.unlink()
        return True


class LocalFaceRecognition:
    """Enrollment and unknown-safe matching over frames supplied by FaceTracker."""

    def __init__(self, model_path: str | Path | None = None,
                 store: FaceProfileStore | None = None, engine: FeatureEngine | None = None,
                 *, threshold: float | None = None, margin: float | None = None,
                 min_face_px: int | None = None, min_confidence: float | None = None,
                 threshold_calibrated: bool | None = None) -> None:
        self.model_path = model_path or os.getenv("CUTY_SFACE_MODEL", "")
        self.store = store or FaceProfileStore()
        self.engine = engine
        self.threshold = float(threshold if threshold is not None else os.getenv("CUTY_FACE_MATCH_THRESHOLD", "0.363"))
        self.margin = float(margin if margin is not None else os.getenv("CUTY_FACE_MATCH_MARGIN", "0.04"))
        self.min_face_px = int(min_face_px if min_face_px is not None else os.getenv("CUTY_FACE_MIN_SIZE", "48"))
        self.min_confidence = float(min_confidence if min_confidence is not None else os.getenv("CUTY_FACE_MIN_CONFIDENCE", "0.75"))
        calibrated_value = os.getenv("CUTY_FACE_MATCH_CALIBRATED", "0").strip().lower()
        self.threshold_calibrated = (calibrated_value in {"1", "true", "yes", "on"}
                                     if threshold_calibrated is None else threshold_calibrated)
        if not 0 < self.threshold <= 1 or not 0 <= self.margin <= 1:
            raise ValueError("Los umbrales coseno deben estar en el rango 0..1")
        if self.min_face_px < 1 or not 0 <= self.min_confidence <= 1:
            raise ValueError("Calidad mínima de rostro inválida")

    def _engine(self) -> FeatureEngine:
        if self.engine is None:
            if not self.model_path:
                raise RecognitionUnavailable("SFace no está configurado; define CUTY_SFACE_MODEL en el Pi")
            self.engine = OpenCVSFace(self.model_path)
        return self.engine

    def _embedding(self, observation: FaceObservation) -> np.ndarray:
        if not isinstance(observation.color_bgr, np.ndarray):
            raise RecognitionUnavailable("FaceTracker no entregó imagen en color")
        if len(observation.detections) != 1:
            raise RecognitionUnavailable("Necesito ver exactamente un rostro para registrar o reconocer")
        face = observation.detections[0]
        if face.score < self.min_confidence or min(face.w, face.h) < self.min_face_px:
            raise RecognitionUnavailable("El rostro se ve demasiado pequeño o poco claro")
        return self._engine().embed(observation.color_bgr, face)

    def enroll(self, name: str, observations: Sequence[FaceObservation]) -> str:
        name = _safe_name(name)
        if not 3 <= len(observations) <= 8:
            raise RecognitionUnavailable("Se requieren de 3 a 8 capturas distintas para el registro")
        vectors = [self._embedding(observation) for observation in observations]
        if any(vector.shape != vectors[0].shape for vector in vectors):
            raise RecognitionUnavailable("SFace produjo dimensiones inconsistentes")
        profiles = self.store.load()
        profiles[name] = vectors
        if len(profiles) > 10:
            raise RecognitionUnavailable("El límite local es de 10 perfiles")
        self.store.save(profiles)
        return name

    def identify(self, observation: FaceObservation) -> dict[str, object]:
        if not self.threshold_calibrated:
            raise RecognitionUnavailable(
                "El umbral de coincidencia no se ha calibrado para esta cámara y su iluminación"
            )
        query = self._embedding(observation)
        profiles = self.store.load()
        if not profiles:
            return {"known": False, "name": None, "score": None}
        engine = self._engine()
        ranked = []
        for name, templates in profiles.items():
            scores = sorted((engine.compare(query, template) for template in templates), reverse=True)
            top = scores[:min(3, len(scores))]
            ranked.append((sum(top) / len(top), name))
        ranked.sort(reverse=True)
        best_score, best_name = ranked[0]
        runner_up = ranked[1][0] if len(ranked) > 1 else -1.0
        known = best_score >= self.threshold and (
            len(ranked) == 1 or best_score - runner_up >= self.margin
        )
        return {"known": known, "name": best_name if known else None,
                "score": float(best_score)}

    def forget(self, name: str | None = None) -> bool:
        if name is None:
            return self.store.forget_all()
        return self.store.forget_profile(name)


def mask_faces_and_encode(observation: FaceObservation, *, jpeg_quality: int = 72) -> bytes:
    """Mask detected faces in memory and return one compact JPEG for Gemini."""
    if not isinstance(observation.color_bgr, np.ndarray):
        raise RecognitionUnavailable("No hay imagen en color para describir")
    try:
        import cv2
        image = observation.color_bgr.copy()
        height, width = image.shape[:2]
        for face in observation.detections:
            pad_x, pad_y = int(face.w * 0.25), int(face.h * 0.25)
            x0, y0 = max(0, face.x - pad_x), max(0, face.y - pad_y)
            x1, y1 = min(width, face.x + face.w + pad_x), min(height, face.y + face.h + pad_y)
            cv2.rectangle(image, (x0, y0), (x1, y1), (32, 32, 32), thickness=-1)
        ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
        if not ok:
            raise RecognitionUnavailable("OpenCV no pudo codificar el fotograma")
        return bytes(encoded)
    except RecognitionUnavailable:
        raise
    except Exception as exc:
        raise RecognitionUnavailable(f"No se pudo preparar una imagen de visión privada: {exc}") from exc
