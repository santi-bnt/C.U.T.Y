"""Short, cached Spanish asides; never make an extra AI request during a turn."""

from __future__ import annotations

import asyncio
import io
import logging
import random

from cuty.audio.speaker import Speaker

PHRASES = (
    "Estoy conectando los puntitos.",
    "Un segundo, estoy ordenando mis ideas.",
    "Mis neuronas digitales están haciendo magia.",
    "Déjame darle una vuelta a eso.",
    "Estoy cocinando una idea.",
    "A ver, déjame pensar tantito.",
    "Estoy desenredando los cables de mi imaginación.",
    "Buena pregunta, voy a pensarlo.",
)
VOICE = "es-MX-DaliaNeural"
CHUNK_BYTES = 960  # 20 ms, mono PCM16 at 24 kHz.


def decode_mp3(audio: bytes) -> bytes:
    import av

    resampler = av.AudioResampler(format="s16", layout="mono", rate=24_000)
    chunks = []
    with av.open(io.BytesIO(audio), format="mp3") as container:
        for frame in container.decode(audio=0):
            for output in resampler.resample(frame):
                chunks.append(bytes(output.planes[0])[:output.samples * 2])
        for output in resampler.resample(None):
            chunks.append(bytes(output.planes[0])[:output.samples * 2])
    pcm = b"".join(chunks)
    if not pcm or len(pcm) % 2:
        raise ValueError("Invalid thinking phrase audio")
    return pcm


async def synthesize(phrase: str) -> bytes:
    import edge_tts

    audio = bytearray()
    voice = edge_tts.Communicate(phrase, VOICE, rate="+8%", volume="-10%")
    async for event in voice.stream():
        if event["type"] == "audio":
            audio.extend(event["data"])
    return await asyncio.to_thread(decode_mp3, bytes(audio))


class ThinkingVoice:
    def __init__(self, *, delay: float = 1.8, interval: float = 5.0) -> None:
        self.delay = delay
        self.interval = interval
        self.clips: dict[str, bytes] = {}
        self._last: str | None = None
        self._log = logging.getLogger("VOZ")

    async def prepare(self) -> None:
        """Prepare in the background; only these fixed phrases go to Edge TTS."""
        for phrase in PHRASES:
            try:
                self.clips[phrase] = await asyncio.wait_for(synthesize(phrase), 6)
            except Exception as exc:
                self._log.warning("Frases de espera no disponibles: %s", exc)
                break  # Keep any clips already prepared; don't delay the main app.
        if self.clips:
            self._log.info("%d frases de espera listas en español", len(self.clips))

    def choose(self) -> tuple[str, bytes] | None:
        choices = [phrase for phrase in self.clips if phrase != self._last]
        if not choices:
            choices = list(self.clips)
        if not choices:
            return None
        phrase = random.choice(choices)
        self._last = phrase
        return phrase, self.clips[phrase]

    async def run(self, speaker: Speaker, stop: asyncio.Event) -> None:
        # This task is joined before the answer uses the same speaker. Never
        # cancel a write running in a thread: let its tiny chunk finish first.
        for index in range(2):
            try:
                await asyncio.wait_for(stop.wait(), self.delay if index == 0 else self.interval)
                return
            except TimeoutError:
                pass
            clip = self.choose()
            if clip is None or stop.is_set():
                return
            phrase, pcm = clip
            self._log.info("Pensando: %s", phrase)
            for offset in range(0, len(pcm), CHUNK_BYTES):
                if stop.is_set():
                    return
                await speaker.write(pcm[offset:offset + CHUNK_BYTES])
                await asyncio.sleep(0)
