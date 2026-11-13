import asyncio
import os
import stat
import sys
import types

import numpy as np
import pytest

from cuty.brain.conversation import ConversationService
from cuty.brain.states import State, StateMachine
from cuty.face.expression_sink import ExpressionController
from cuty.llm.provider import AIEvent, EventKind
from cuty.vision.face_detector import Detection
from cuty.vision.face_tracker import FaceObservation
from cuty.vision.recognition import FaceProfileStore, LocalFaceRecognition, mask_faces_and_encode
from cuty.vision.voice_commands import (
    confirmed_enrollment_name, confirmed_forget, is_explicit_cancel,
    may_be_vision_intent, vision_intent,
)


class Microphone:
    async def chunks(self, stop):
        yield b"\0\0" * 64
        stop.set()


class Speaker:
    def __init__(self):
        self.audio = []

    async def open(self):
        pass

    async def close(self):
        pass

    async def write(self, data):
        self.audio.append(data)


class Provider:
    def __init__(self, events):
        self.events = list(events)
        self.spoken = []
        self.images = []

    async def start_turn(self): pass
    async def send_audio(self, data): pass
    async def finish_input(self): pass
    async def receive(self): return self.events.pop(0)
    async def continue_response(self): pass
    async def submit_tool_result(self, call_id, output): pass

    async def describe_image(self, image, *, question):
        self.images.append((image, question))
        return "Veo una taza sobre el escritorio."

    async def speak_text(self, text):
        self.spoken.append(text)
        self.events.extend([
            AIEvent(EventKind.AUDIO, audio=b"\x02\x00" * 64),
            AIEvent(EventKind.DONE),
        ])


class Sink:
    def set_expression(self, *_args): pass


def make_service(events, vision):
    provider = Provider(events)
    speaker = Speaker()
    expressions = ExpressionController(Sink())
    service = ConversationService(
        provider, Microphone(), speaker, StateMachine(expressions.on_state),
        expressions, vision=vision,
    )
    return service, provider, speaker


def test_bilingual_local_intents_and_explicit_consent_phrases():
    assert vision_intent("Cuty, ¿qué estás viendo?") == "describe"
    assert vision_intent("Cuty, what do you see?") == "describe"
    assert vision_intent("recuerda mi rostro") == "enroll"
    assert vision_intent("¿quién soy?") == "identify"
    assert vision_intent("olvida mi cara") == "forget"
    assert may_be_vision_intent("Cuty")
    assert may_be_vision_intent("Cuty, qué estás")
    assert not may_be_vision_intent("Cuty, pon música")
    assert confirmed_enrollment_name("Confirmo guardar mi rostro y llámame Santi BNT") == "Santi Bnt"
    assert confirmed_enrollment_name("Confirmo guardar mi rostro, me llamo José") == "José"
    assert confirmed_enrollment_name("guarda mi rostro, me llamo Santi") is None
    assert confirmed_forget("Confirmo, olvida mi rostro")
    assert not confirmed_forget("olvida mi rostro")
    assert is_explicit_cancel("cancela")


def test_visual_voice_request_suppresses_generic_model_audio_and_speaks_grounded_result():
    class Vision:
        def capture_redacted_jpeg(self): return b"synthetic-redacted-jpeg"

    service, provider, speaker = make_service([
        # Provider's existing order is audio before the input transcript.
        AIEvent(EventKind.AUDIO, audio=b"\x01\x00" * 64),
        AIEvent(EventKind.INPUT_TRANSCRIPT, transcript="Cuty, ¿qué estás viendo?"),
        AIEvent(EventKind.DONE),
    ], Vision())
    assert asyncio.run(service.run_turn(asyncio.Event()))
    assert provider.images == [(b"synthetic-redacted-jpeg", "¿Qué estás viendo?")]
    assert speaker.audio == [b"\x02\x00" * 64]
    assert provider.spoken == ["Veo una taza sobre el escritorio."]


def test_split_visual_command_never_leaks_the_generic_audio_before_full_transcript():
    class Vision:
        def capture_redacted_jpeg(self): return b"synthetic-redacted-jpeg"

    service, provider, speaker = make_service([
        AIEvent(EventKind.AUDIO, audio=b"\x01\x00" * 64),
        AIEvent(EventKind.INPUT_TRANSCRIPT, transcript="Cuty"),
        AIEvent(EventKind.INPUT_TRANSCRIPT, transcript="qué estás"),
        AIEvent(EventKind.INPUT_TRANSCRIPT, transcript="viendo"),
        AIEvent(EventKind.DONE),
    ], Vision())
    asyncio.run(service.run_turn(asyncio.Event()))
    assert speaker.audio == [b"\x02\x00" * 64]
    assert provider.images and provider.spoken == ["Veo una taza sobre el escritorio."]


def test_failed_vision_provider_keeps_voice_process_alive_and_reports_fallback():
    from cuty.llm.provider import ProviderError

    class Vision:
        def capture_redacted_jpeg(self): return b"synthetic-redacted-jpeg"

    service, provider, speaker = make_service([
        AIEvent(EventKind.INPUT_TRANSCRIPT, transcript="¿Qué estás viendo?"),
        AIEvent(EventKind.DONE),
    ], Vision())

    async def offline(*_args, **_kwargs): raise ProviderError("offline")

    provider.describe_image = offline
    assert asyncio.run(service.run_turn(asyncio.Event()))
    assert provider.spoken and "No pude completar" in provider.spoken[0]
    assert speaker.audio == [b"\x02\x00" * 64]
    assert service.state.current == State.IDLE


def test_enrollment_requires_a_second_explicit_confirmation():
    class Vision:
        def __init__(self): self.saved = []
        def enroll(self, name):
            self.saved.append(name)
            return {"name": name, "samples": 5}

    vision = Vision()
    service, provider, _ = make_service([
        AIEvent(EventKind.INPUT_TRANSCRIPT, transcript="Cuty, recuerda mi rostro"),
        AIEvent(EventKind.DONE),
    ], vision)
    asyncio.run(service.run_turn(asyncio.Event()))
    assert service._face_consent == "enroll"
    assert not vision.saved
    provider.events.extend([
        AIEvent(EventKind.INPUT_TRANSCRIPT,
                transcript="Confirmo guardar mi rostro y llámame Santi"),
        AIEvent(EventKind.DONE),
    ])
    asyncio.run(service.run_turn(asyncio.Event()))
    assert vision.saved == ["Santi"]
    assert service._face_consent is None


def test_cancel_pending_face_enrollment_never_calls_storage():
    class Vision:
        def enroll(self, _name): raise AssertionError("must not save")

    service, provider, _ = make_service([
        AIEvent(EventKind.INPUT_TRANSCRIPT, transcript="recuerda mi rostro"),
        AIEvent(EventKind.DONE),
    ], Vision())
    asyncio.run(service.run_turn(asyncio.Event()))
    provider.events.extend([
        AIEvent(EventKind.INPUT_TRANSCRIPT, transcript="cancela"),
        AIEvent(EventKind.DONE),
    ])
    asyncio.run(service.run_turn(asyncio.Event()))
    assert service._face_consent is None
    assert "No guardaré ni borraré" in provider.spoken[-1]


def test_embeddings_store_without_images_and_unknown_below_match_threshold(tmp_path):
    class Engine:
        def embed(self, image, detection):
            return np.array([float(image[0, 0, 0]), 1.0] + [0.0] * 30, np.float32)
        def compare(self, first, second):
            return float(np.dot(first, second) / (np.linalg.norm(first) * np.linalg.norm(second)))

    store = FaceProfileStore(tmp_path / "private" / "profiles.json", owner="missing-test-user")
    recognizer = LocalFaceRecognition(store=store, engine=Engine(), threshold=0.9, margin=0.1,
                                     threshold_calibrated=True)
    face = Detection(10, 10, 80, 80, 0.99, landmarks=tuple(float(v) for v in range(10)))
    samples = [FaceObservation(i, float(i), np.full((120, 120, 3), 255, np.uint8), (face,))
               for i in range(1, 4)]
    recognizer.enroll("Santi", samples)
    assert recognizer.identify(samples[0])["name"] == "Santi"
    other = FaceObservation(4, 4.0, np.zeros((120, 120, 3), np.uint8), (face,))
    assert recognizer.identify(other)["known"] is False
    other_samples = [FaceObservation(i + 10, float(i + 10),
                                     np.zeros((120, 120, 3), np.uint8), (face,))
                     for i in range(1, 4)]
    recognizer.enroll("Otra Persona", other_samples)
    assert recognizer.forget("Santi")
    assert set(store.load()) == {"Otra Persona"}
    raw = store.path.read_text(encoding="utf-8")
    assert "\"profiles\"" in raw and "image" not in raw and "jpeg" not in raw
    if os.name == "posix":
        assert stat.S_IMODE(store.path.stat().st_mode) == 0o600
        assert stat.S_IMODE(store.path.parent.stat().st_mode) == 0o700


def test_un_calibrated_threshold_fails_closed_even_with_a_saved_template(tmp_path):
    class Engine:
        def embed(self, _image, _detection): return np.ones(32, dtype=np.float32)
        def compare(self, _first, _second): return 1.0

    store = FaceProfileStore(tmp_path / "profiles.json", owner="missing-test-user")
    face = Detection(10, 10, 80, 80, 0.99, landmarks=tuple(float(v) for v in range(10)))
    observation = FaceObservation(1, 1.0, np.full((120, 120, 3), 255, np.uint8), (face,))
    recognizer = LocalFaceRecognition(store=store, engine=Engine())
    recognizer.enroll("Santi", [observation] * 3)
    from cuty.vision.recognition import RecognitionUnavailable
    with pytest.raises(RecognitionUnavailable, match="no se ha calibrado"):
        recognizer.identify(observation)


def test_redacted_jpeg_masks_detected_faces_in_memory():
    image = np.full((100, 120, 3), (40, 120, 210), dtype=np.uint8)
    face = Detection(30, 20, 40, 50, 0.99)
    observation = FaceObservation(1, 1.0, image, (face,))

    class FakeCV2(types.ModuleType):
        IMWRITE_JPEG_QUALITY = 1
        def rectangle(self, target, first, second, color, thickness):
            assert thickness == -1
            target[first[1]:second[1] + 1, first[0]:second[0] + 1] = color
        def imencode(self, _extension, target, _options):
            self.encoded = target.copy()
            return True, np.array([1, 2, 3], dtype=np.uint8)

    cv2 = FakeCV2("cv2")
    old_cv2 = sys.modules.get("cv2")
    sys.modules["cv2"] = cv2
    try:
        encoded = mask_faces_and_encode(observation)
    finally:
        if old_cv2 is None:
            sys.modules.pop("cv2", None)
        else:
            sys.modules["cv2"] = old_cv2
    assert encoded == bytes([1, 2, 3])
    assert cv2.encoded[45, 50].max() < 70
    assert cv2.encoded[5, 5].mean() > 90
    assert np.all(image[45, 50] == (40, 120, 210))  # source frame was not mutated
