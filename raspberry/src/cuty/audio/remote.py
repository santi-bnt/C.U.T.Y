"""Play Pi reply audio on a PC over a local TCP socket forwarded by SSH.

Wire format: fixed PCM16/24 kHz/mono header, then length-prefixed chunks.
Each chunk is acknowledged after playback so the sender cannot queue an
unbounded reply. Bind the receiver to localhost and use an SSH reverse tunnel.
"""

from __future__ import annotations

import asyncio
import struct

from cuty.audio.devices import AudioDeviceError
from cuty.audio.speaker import SoundDeviceSpeaker, Speaker

HEADER = b"CUTY_PCM16_24000_MONO\n"
MAX_CHUNK = 48_000  # One second of mono PCM16.
TIMEOUT = 15


def parse_endpoint(value: str) -> tuple[str, int]:
    host, separator, port = value.rpartition(":")
    if not separator or not host or not port.isdigit() or not 1 <= int(port) <= 65535:
        raise AudioDeviceError("Remote audio address must be host:port, e.g. 127.0.0.1:8765.")
    return host, int(port)


class RemoteSpeaker:
    def __init__(self, address: str) -> None:
        self.address = parse_endpoint(address)
        self._reader = None
        self._writer = None

    async def _ack(self) -> None:
        if await asyncio.wait_for(self._reader.readexactly(1), TIMEOUT) != b"K":
            raise AudioDeviceError("PC audio receiver rejected the stream.")

    async def open(self) -> None:
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(*self.address), TIMEOUT,
            )
            self._writer.write(HEADER)
            await self._writer.drain()
            await self._ack()
        except (OSError, EOFError, TimeoutError, AudioDeviceError) as exc:
            await self.close()
            raise AudioDeviceError(f"Cannot connect to PC audio receiver: {exc}") from exc

    async def write(self, pcm16: bytes) -> None:
        if self._writer is None:
            raise AudioDeviceError("Remote speaker is not open.")
        if len(pcm16) % 2:
            raise AudioDeviceError("PCM16 audio must contain complete 16-bit samples.")
        try:
            for offset in range(0, len(pcm16), MAX_CHUNK):
                chunk = pcm16[offset:offset + MAX_CHUNK]
                self._writer.write(struct.pack("!I", len(chunk)) + chunk)
                await self._writer.drain()
                await self._ack()
        except (OSError, EOFError, TimeoutError) as exc:
            raise AudioDeviceError(f"PC audio playback disconnected: {exc}") from exc

    async def close(self) -> None:
        if self._writer is not None:
            writer, self._writer = self._writer, None
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass
        self._reader = None


async def receive_audio(reader, writer, speaker: Speaker) -> None:
    """Receive one connection; only open hardware after validating the header."""
    opened = False
    try:
        if await asyncio.wait_for(reader.readexactly(len(HEADER)), TIMEOUT) != HEADER:
            raise AudioDeviceError("Invalid remote audio format.")
        await speaker.open()
        opened = True
        writer.write(b"K")
        await writer.drain()
        while True:
            size = struct.unpack("!I", await reader.readexactly(4))[0]
            if size == 0 or size > MAX_CHUNK or size % 2:
                raise AudioDeviceError("Invalid remote audio chunk size.")
            await speaker.write(await reader.readexactly(size))
            writer.write(b"K")
            await writer.drain()
    except asyncio.IncompleteReadError as exc:
        if exc.partial:
            print("PC audio: truncated stream.", flush=True)
    except (OSError, TimeoutError, AudioDeviceError) as exc:
        print(f"PC audio: {exc}", flush=True)
    finally:
        try:
            if opened:
                await speaker.close()
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass


async def serve_audio(device: int, port: int = 8765) -> None:
    busy = False

    async def accept(reader, writer):
        nonlocal busy
        if busy:
            writer.close()
            await writer.wait_closed()
            return
        busy = True
        try:
            await receive_audio(reader, writer, SoundDeviceSpeaker(device))
        finally:
            busy = False

    server = await asyncio.start_server(accept, "127.0.0.1", port)
    print(f"PC audio ready on 127.0.0.1:{port}. Keep this terminal open.", flush=True)
    async with server:
        await server.serve_forever()
