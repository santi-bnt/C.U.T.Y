"""Loopback-only touchscreen requests for music and microphone control."""

from __future__ import annotations

import asyncio
import os


def interrupt_port() -> int:
    try:
        port = int(os.getenv("CUTY_MUSIC_INTERRUPT_PORT", "5010"))
    except ValueError as exc:
        raise ValueError("CUTY_MUSIC_INTERRUPT_PORT must be a valid UDP port") from exc
    if not 1024 <= port <= 65535:
        raise ValueError("CUTY_MUSIC_INTERRUPT_PORT must be from 1024 to 65535")
    return port


class _InterruptProtocol(asyncio.DatagramProtocol):
    def __init__(self, event: asyncio.Event, armed: asyncio.Event,
                 next_event: asyncio.Event | None = None) -> None:
        self.event = event
        self.armed = armed
        self.next_event = next_event

    def datagram_received(self, data: bytes, addr) -> None:
        if data == b"listen" and self.armed.is_set():
            self.event.set()
        elif data == b"next" and self.armed.is_set() and self.next_event is not None:
            self.next_event.set()


async def open_interrupt_listener(event: asyncio.Event, armed: asyncio.Event,
                                  next_event: asyncio.Event | None = None):
    """Bind a private-to-this-host listener; the port is not exposed to LAN."""
    loop = asyncio.get_running_loop()
    return await loop.create_datagram_endpoint(
        lambda: _InterruptProtocol(event, armed, next_event),
        local_addr=("127.0.0.1", interrupt_port()),
    )
