"""Exercise TCP framing and disconnects without audio hardware or AI APIs."""

import asyncio
import struct

import pytest

from cuty.audio.devices import AudioDeviceError
from cuty.audio.remote import HEADER, MAX_CHUNK, RemoteSpeaker, parse_endpoint, receive_audio


class Speaker:
    def __init__(self):
        self.data = bytearray()
        self.closed = False

    async def open(self):
        pass

    async def write(self, data):
        self.data.extend(data)

    async def close(self):
        self.closed = True


def test_remote_audio_preserves_pcm_and_closes_after_disconnect():
    async def run():
        speaker = Speaker()
        finished = asyncio.Event()

        async def accept(reader, writer):
            try:
                await receive_audio(reader, writer, speaker)
            finally:
                finished.set()

        server = await asyncio.start_server(accept, "127.0.0.1", 0)
        async with server:
            port = server.sockets[0].getsockname()[1]
            client = RemoteSpeaker(f"127.0.0.1:{port}")
            try:
                await client.open()
                pcm = b"\x00\x01\xff\x7f" * MAX_CHUNK
                await client.write(pcm)
                assert speaker.data == pcm
            finally:
                await client.close()
            await asyncio.wait_for(finished.wait(), 2)
            assert speaker.closed

    asyncio.run(run())


@pytest.mark.parametrize("size", [0, 3, MAX_CHUNK + 2])
def test_receiver_rejects_invalid_frame_without_playing(size):
    async def run():
        speaker = Speaker()
        reader = asyncio.StreamReader()
        reader.feed_data(HEADER + struct.pack("!I", size))
        reader.feed_eof()

        class Writer:
            def write(self, data):
                pass

            async def drain(self):
                pass

            def close(self):
                pass

            async def wait_closed(self):
                pass

        await receive_audio(reader, Writer(), speaker)
        assert not speaker.data
        assert speaker.closed

    asyncio.run(run())


@pytest.mark.parametrize("address", ["localhost", ":8765", "localhost:0", "localhost:65536", "localhost:no"])
def test_invalid_remote_address(address):
    with pytest.raises(AudioDeviceError, match="host:port"):
        parse_endpoint(address)
