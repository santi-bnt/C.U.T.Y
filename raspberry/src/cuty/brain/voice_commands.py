"""Explicit local exit commands; never match a word inside a longer question."""

import re
import unicodedata


def wants_menu(transcript: str) -> bool:
    normalized = unicodedata.normalize("NFKD", transcript.casefold())
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    words = re.findall(r"[a-z]+", normalized)
    phrase = " ".join(words)
    phrase = re.sub(r"\bc u t y\b", "cuty", phrase)
    phrase = re.sub(r"^(?:oye )?(?:cuty|cuti|kuty|kuti)\s+", "", phrase)
    for suffix in (" por favor",):
        if phrase.endswith(suffix):
            phrase = phrase[:-len(suffix)]
    if phrase.endswith((" cuty", " cuti", " kuty", " kuti")) and not phrase.endswith((" de cuty", " de cuti", " de kuty", " de kuti")):
        phrase = phrase[:-5]
    return phrase in {
        "salir", "quiero salir", "quiero salir de cuty", "quiero salir de cuti", "sal del modo conversacion",
        "quiero salir de kuti", "quiero salir de kuty", "salir al menu", "salir al menu principal",
        "volver al menu", "volver al menu principal", "vuelve al menu", "vuelve al menu principal",
        "regresa al menu", "regresa al menu principal", "quiero volver al menu",
        "quiero volver al menu principal", "quiero regresar al menu", "menu principal",
        "terminar conversacion", "termina la conversacion", "exit", "quit",
    }
