"""Deterministic bilingual face and visual query intents plus consent parsing."""

from __future__ import annotations

import re
import unicodedata

_INTENT_PHRASES = (
    "que estas viendo", "que ves", "what are you seeing", "what do you see",
    "recuerda mi rostro", "recuerda mi cara", "remember my face", "learn my face",
    "quien soy", "quien es esta persona", "who am i", "who is this",
    "olvida mi rostro", "olvida mi cara", "forget my face", "forget my face data",
)


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    plain = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(re.sub(r"[^a-z0-9' -]", " ", plain).split())


def vision_intent(transcript: str) -> str | None:
    text = normalize(transcript)
    if any(phrase in text for phrase in (
        "que estas viendo", "que ves", "what are you seeing", "what do you see",
    )) or re.search(r"\bque(?:\s+[a-z0-9']+){0,4}\s+estas viendo\b", text):
        return "describe"
    if any(phrase in text for phrase in (
        "recuerda mi rostro", "recuerda mi cara", "remember my face", "learn my face",
    )):
        return "enroll"
    if any(phrase in text for phrase in (
        "quien soy", "quien es esta persona", "who am i", "who is this",
    )):
        return "identify"
    if any(phrase in text for phrase in (
        "olvida mi rostro", "olvida mi cara", "forget my face", "forget my face data",
    )):
        return "forget"
    return None


def may_be_vision_intent(transcript: str) -> bool:
    """Hold early model audio while a split transcript may still form a face command."""
    text = normalize(transcript)
    if not text:
        return False
    words = text.split()
    if words[-1] == "cuty" and len(words) <= 2:
        return True
    if re.search(r"\bque(?:\s+[a-z0-9']+){0,4}\s+estas(?:\s+viendo)?$", text):
        return True
    for phrase in _INTENT_PHRASES:
        phrase_words = phrase.split()
        for size in range(1, min(len(words), len(phrase_words)) + 1):
            if words[-size:] == phrase_words[:size]:
                return True
    return False


def is_explicit_cancel(transcript: str) -> bool:
    return normalize(transcript) in {
        "no", "no gracias", "cancela", "cancelar", "cancel", "no quiero", "nevermind",
    }


def confirmed_enrollment_name(transcript: str) -> str | None:
    text = normalize(transcript)
    has_confirmation = any(word in text.split() for word in ("confirmo", "confirmar", "confirm", "consiento"))
    if not has_confirmation or not any(word in text for word in ("rostro", "cara", "face")):
        return None
    match = re.search(
        r"\b(?:ll[aá]mame|me llamo|call me|my name is)\s+(.+?)\s*[.!?,;:]*$",
        " ".join(transcript.strip().split()), re.IGNORECASE,
    )
    if not match:
        return None
    words = match.group(1).strip().split()
    if not 1 <= len(words) <= 3 or any(
        not all(character.isalpha() or character in "-'" for character in word)
        for word in words
    ):
        return None
    name = " ".join(word.capitalize() for word in words)
    return name if 1 <= len(name) <= 40 else None


def confirmed_forget(transcript: str) -> bool:
    text = normalize(transcript)
    explicit = any(word in text.split() for word in ("confirmo", "confirmar", "confirm", "autorizo"))
    refers_to_face = any(phrase in text for phrase in (
        "olvida mi rostro", "olvida mi cara", "borra mi rostro", "borra mi cara",
        "forget my face", "delete my face",
    ))
    return explicit and refers_to_face
