"""Deterministic Spanish and English music command parsing."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class MusicCommand:
    action: str
    query: str | None = None
    volume: int | None = None


def _normalize(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text.casefold())
    plain = "".join(char for char in folded if not unicodedata.combining(char))
    plain = re.sub(r"[^a-z0-9%]+", " ", plain)
    plain = re.sub(r"\s+", " ", plain).strip()
    # Streaming transcription can occasionally duplicate an entire utterance.
    words = plain.split()
    if len(words) >= 4 and len(words) % 2 == 0:
        midpoint = len(words) // 2
        if words[:midpoint] == words[midpoint:]:
            plain = " ".join(words[:midpoint])
    # "Cuty" is sometimes transcribed as "Siri" by the microphone recognizer.
    plain = re.sub(r"^(?:(?:oye|hey) )?(?:cuty|cuti|kuty|kuti|siri)\s+", "", plain)
    return plain


def parse_music_command(text: str) -> MusicCommand | None:
    phrase = _normalize(text)
    if not phrase:
        return None
    if re.search(r"\b(?:modo(?: de)? (?:la )?musica|modo spotify|music mode|spotify mode)\b", phrase):
        return MusicCommand("phone_mode")
    if re.search(r"\b(pausa|pausa la musica|pause|pause the music)\b", phrase):
        return MusicCommand("pause")
    if re.search(r"\b(continua|reanuda|resume|continue)\b", phrase):
        return MusicCommand("resume")
    if re.search(r"\b(detente|deten|para la musica|deja de reproducir|deja de poner musica|deten la reproduccion|stop|stop the music|stop playing)\b", phrase):
        return MusicCommand("stop")
    if re.search(r"\b(otra cancion|siguiente|next|next song)\b", phrase):
        return MusicCommand("next")
    if re.search(r"\b(anterior|previous|previous song)\b", phrase):
        return MusicCommand("previous")
    if re.search(r"\b(que cancion|que esta sonando|what song|current track|now playing)\b", phrase):
        return MusicCommand("get_current_track")
    volume_match = re.search(r"\b(?:volumen|volume)\s+(?:al\s+)?(\d{1,3})\s*(%|por ciento|percent)?\b", phrase)
    if volume_match:
        value = int(volume_match.group(1))
        if value <= 100:
            return MusicCommand("set_volume", volume=value)
        return None
    if re.search(r"\b(sub(e|e el)|aumenta|mas volumen|turn it up|increase volume|volume up)\b", phrase):
        return MusicCommand("volume_up")
    if re.search(r"\b(baja|reduce|menos volumen|turn it down|decrease volume|volume down)\b", phrase):
        return MusicCommand("volume_down")
    match = re.search(
        r"\b(?:me puedes poner|puedes ponerme|puedes poner|me pones|ponme|pon|"
        r"reproduce|reproducir|busca|can you play|could you play|play|put on|search for)\s+(.+)$",
        phrase,
    )
    if match:
        query = match.group(1).strip()
        query = re.sub(r"^(?:(?:(?:la|una) )?cancion(?: de)?|musica de|music by|song by|music|a song)\s+", "", query)
        query = re.sub(r"\s+(?:por favor|please)$", "", query).strip()
        return MusicCommand("search", query=query[:160]) if query else None
    return None
