"""Explicit local exit commands; never match a word inside a longer question."""

import re
import unicodedata


def wants_menu(transcript: str) -> bool:
    normalized = unicodedata.normalize("NFKD", transcript.casefold())
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    words = re.findall(r"[a-z]+", normalized)
    phrase = " ".join(words)
    if phrase.startswith(("cuty ", "cuti ")):
        phrase = phrase[5:]
    for suffix in (" por favor",):
        if phrase.endswith(suffix):
            phrase = phrase[:-len(suffix)]
    if phrase.endswith((" cuty", " cuti")) and not phrase.endswith((" de cuty", " de cuti")):
        phrase = phrase[:-5]
    return phrase in {
        "salir", "quiero salir", "quiero salir de cuty", "quiero salir de cuti", "sal del modo conversacion",
        "volver al menu", "volver al menu principal", "vuelve al menu", "vuelve al menu principal",
        "regresa al menu", "regresa al menu principal", "quiero volver al menu",
        "quiero volver al menu principal", "quiero regresar al menu", "menu principal",
        "terminar conversacion", "termina la conversacion", "exit", "quit",
    }
