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
    phrase_words = phrase.split()
    if len(phrase_words) >= 4 and len(phrase_words) % 2 == 0:
        midpoint = len(phrase_words) // 2
        if phrase_words[:midpoint] == phrase_words[midpoint:]:
            phrase = " ".join(phrase_words[:midpoint])
    for suffix in (" por favor",):
        if phrase.endswith(suffix):
            phrase = phrase[:-len(suffix)]
    if phrase.endswith((" cuty", " cuti", " kuty", " kuti")) and not phrase.endswith((" de cuty", " de cuti", " de kuty", " de kuti")):
        phrase = phrase[:-5]
    return phrase in {
        "salir", "quiero salir", "quiero salir de cuty", "quiero salir de cuti", "sal del modo conversacion",
        "salir del modo musica", "salir del modo de la musica", "salir del modo la musica",
        "salir de modo musica", "salir de la musica", "quiero salir del modo musica",
        "quiero salir del modo de la musica", "quiero salir de modo musica",
        "quiero salir de la musica", "quiero salirme", "me quiero salir",
        "sal del modo musica", "quita el modo musica", "quitar el modo musica",
        "desactiva el modo musica", "salir de spotify",
        "quiero salir de kuti", "quiero salir de kuty", "salir al menu", "salir al menu principal",
        "volver al menu", "volver al menu principal", "vuelve al menu", "vuelve al menu principal",
        "regresa al menu", "regresa al menu principal", "quiero volver al menu",
        "quiero volver al menu principal", "quiero regresar al menu", "menu principal",
        "terminar conversacion", "termina la conversacion", "exit", "quit",
    }
