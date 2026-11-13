import asyncio

import pytest

from cuty.audio.volume import VoiceVolume, VolumeSpeaker
from cuty.brain.volume_commands import VolumeCommand, parse_volume_command
from cuty.brain.conversation import ConversationService
from cuty.brain.states import StateMachine
from cuty.face.expression_sink import ExpressionController
from cuty.llm.provider import AIEvent, EventKind


@pytest.mark.parametrize(("text", "expected"), [
    ("Cuty, sube el volumen", VolumeCommand("adjust", "active", 10)),
    ("baja el volumen", VolumeCommand("adjust", "active", -10)),
    ("habla más bajito", VolumeCommand("adjust", "voice", -10)),
    ("pon el volumen al 50 por ciento", VolumeCommand("set", "active", 50)),
    ("súbele un 10 %", VolumeCommand("adjust", "active", 10)),
    ("silencio", VolumeCommand("mute", "both")),
    ("activa el sonido", VolumeCommand("unmute", "both")),
    ("baja el volumen de la música", VolumeCommand("adjust", "music", -10)),
    ("turn the music down by 10 percent", VolumeCommand("adjust", "music", -10)),
    ("set voice volume to 35%", VolumeCommand("set", "voice", 35)),
    ("mute", VolumeCommand("mute", "both")),
    ("unmute", VolumeCommand("unmute", "both")),
])
def test_volume_command_parser(text, expected):
    assert parse_volume_command(text) == expected


def test_volume_parser_rejects_out_of_range_and_non_volume_phrases():
    assert parse_volume_command("pon el volumen al 150 por ciento") is None
    assert parse_volume_command("¿qué volumen tiene la música?") is None


def test_voice_volume_clamps_mutes_and_restores_previous_level():
    volume = VoiceVolume(50, 10)
    assert volume.apply((1000).to_bytes(2, "little", signed=True)) == (500).to_bytes(2, "little", signed=True)
    volume.adjust(100)
    assert volume.value == 100
    volume.mute()
    assert volume.apply(b"\xff\x7f") == b"\x00\x00"
    assert volume.unmute() == 100
    with pytest.raises(ValueError):
        volume.set(101)


class _Microphone:
    async def chunks(self, stop):
        yield b"\x00\x00" * 8


class _Speaker:
    def __init__(self):
        self.audio = []

    async def open(self): pass
    async def close(self): pass
    async def write(self, audio): self.audio.append(audio)


class _Provider:
    def __init__(self):
        self.events = [
            AIEvent(EventKind.AUDIO, audio=(1000).to_bytes(2, "little", signed=True) * 4),
            AIEvent(EventKind.INPUT_TRANSCRIPT, transcript="Cuty, habla más bajito"),
            AIEvent(EventKind.AUDIO, audio=(1000).to_bytes(2, "little", signed=True) * 4),
            AIEvent(EventKind.DONE),
        ]

    async def start_turn(self): pass
    async def send_audio(self, audio): pass
    async def finish_input(self): pass
    async def receive(self): return self.events.pop(0)


class _Sink:
    def set_expression(self, *args): pass


def test_command_changes_voice_gain_before_buffered_gemini_audio_plays():
    async def run():
        volume = VoiceVolume(70, 10)
        raw_speaker = _Speaker()
        speaker = VolumeSpeaker(raw_speaker, volume)
        expressions = ExpressionController(_Sink())
        service = ConversationService(
            _Provider(), _Microphone(), speaker, StateMachine(expressions.on_state),
            expressions, voice_volume=volume,
        )
        # run_turn expects the microphone to signal completion.
        class Mic:
            async def chunks(self, stop):
                yield b"\x00\x00" * 8
                stop.set()
        service.microphone = Mic()
        await service.run_turn(__import__("asyncio").Event())
        assert volume.value == 60
        # Both early and subsequent response chunks wait for the recognized command.
        assert len(raw_speaker.audio) == 2
        assert all(audio == (600).to_bytes(2, "little", signed=True) * 4 for audio in raw_speaker.audio)

    asyncio.run(run())


def test_active_target_routes_to_music_and_restores_muted_music_level():
    async def run():
        from cuty.brain.volume_commands import VolumeCommand
        from cuty.music.protocol import PlaybackState

        class Music:
            status = "playing"
            volume = 65

            async def get_playback_state(self):
                return PlaybackState(self.status, None, self.volume)

            async def set_volume(self, value):
                self.volume = value

        music = Music()
        raw_speaker = _Speaker()
        expressions = ExpressionController(_Sink())
        service = ConversationService(
            _Provider(), _Microphone(), raw_speaker, StateMachine(expressions.on_state),
            expressions, music=music, voice_volume=VoiceVolume(40),
        )
        await service._apply_volume_command(VolumeCommand("adjust", "active", 10))
        assert music.volume == 75
        assert service.voice_volume.value == 40
        await service._apply_volume_command(VolumeCommand("mute", "music"))
        assert music.volume == 0
        await service._apply_volume_command(VolumeCommand("unmute", "music"))
        assert music.volume == 75

    asyncio.run(run())
