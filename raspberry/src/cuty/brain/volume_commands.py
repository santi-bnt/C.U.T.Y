"""Deterministic Spanish/English speech volume command parsing."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class VolumeCommand:
    action: str  # set | adjust | mute | unmute
    target: str  # active | voice | music | both
    value: int | None = None


def _normalize(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text.casefold())
    plain = "".join(char for char in folded if not unicodedata.combining(char))
    plain = re.sub(r"[^a-z0-9%]+", " ", plain)
    plain = re.sub(r"\s+", " ", plain).strip()
    return re.sub(r"^(?:(?:oye|hey) )?(?:cuty|cuti|kuty|kuti)\s+", "", plain)


def parse_volume_command(text: str, *, step: int = 10) -> VolumeCommand | None:
    phrase = _normalize(text)
    if not phrase:
        return None

    music = bool(re.search(r"\b(musica|music|cancion|song)\b", phrase))
    voice = bool(re.search(r"\b(voz|voice|habla|hablar|speak|speaks|talk)\b", phrase))
    target = "music" if music else "voice" if voice else "active"

    if re.search(r"\b(silencio|silencia todo|mute|mute everything|silence|silence everything|turn sound off|turn the sound off)\b", phrase):
        return VolumeCommand("mute", "music" if music else "voice" if voice else "both")
    if re.search(r"\b(activa el sonido|activa sonido|activa el audio|quita silencio|unmute|turn sound on|turn the sound on|activate sound|restore sound)\b", phrase):
        return VolumeCommand("unmute", "music" if music else "voice" if voice else "both")

    absolute = re.search(
        r"\b(?:pon|fija|ajusta|set|put)?\s*(?:(?:el )?(?:volumen|volume)(?: (?:de )?(?:la )?(?:musica|music))?|(?:musica|music) volume|(?:voz|voice) volume)\s*(?:al|a|en|to)?\s*(\d{1,3})\s*(?:%|por ciento|percent)?\b",
        phrase,
    )
    if absolute:
        value = int(absolute.group(1))
        return VolumeCommand("set", target, value) if value <= 100 else None

    delta_value = re.search(r"\b(?:un |a |by )?(\d{1,3})\s*(?:%|por ciento|percent)\b", phrase)
    delta = min(100, int(delta_value.group(1))) if delta_value else step
    if re.search(r"\b(sub(e|ele)|subir|aumenta|increase|raise|turn it up|turn up|up|louder|mas alto)\b", phrase):
        return VolumeCommand("adjust", target, delta)
    if re.search(r"\b(baja|bajale|bajar|reduce|decrease|lower|turn it down|turn down|down|quieter|mas bajito|mas bajo)\b", phrase):
        return VolumeCommand("adjust", target, -delta)
    return None
