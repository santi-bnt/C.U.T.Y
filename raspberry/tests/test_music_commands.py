import pytest

from cuty.music.commands import MusicCommand, parse_music_command


@pytest.mark.parametrize(("text", "expected"), [
    ("Cuty, pon 505 de Arctic Monkeys", MusicCommand("search", "505 de arctic monkeys")),
    ("Cuty, reproduce música de Queen", MusicCommand("search", "queen")),
    ("Cuty, pon otra canción", MusicCommand("next")),
    ("Cuty, pausa la música", MusicCommand("pause")),
    ("Cuty, continúa", MusicCommand("resume")),
    ("Cuty, baja el volumen al 30 por ciento", MusicCommand("set_volume", volume=30)),
    ("Cuty, sube el volumen", MusicCommand("volume_up")),
    ("Cuty, ¿qué canción está sonando?", MusicCommand("get_current_track")),
    ("Cuty, stop the music", MusicCommand("stop")),
    ("Cuty, play music by Queen", MusicCommand("search", "music by queen")),
])
def test_bilingual_command_parser(text, expected):
    assert parse_music_command(text) == expected


def test_volume_out_of_range_is_rejected():
    assert parse_music_command("Cuty, set volume to 130 percent") is None

