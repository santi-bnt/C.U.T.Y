"""Tiny UDP link from the voice app to the face on the touchscreen.

The voice app and the touchscreen launcher are separate processes (the
launcher runs as root for the framebuffer). One JSON object per datagram:

    {"v": 1, "type": "expression", "expression": "happy", "intensity": 0.8}
    {"v": 1, "type": "mouth", "level": 0.42}
    {"v": 1, "type": "look", "x": 0.5, "y": 0.5}
    {"v": 1, "type": "blink"}

Sending is fire-and-forget: if the face is not running nothing breaks.

Environment:
    CUTY_FACE_LINK    host:port the voice app sends to (default 127.0.0.1:5005,
                      "off" disables). Use the Pi's IP to drive the face from a PC.
    CUTY_FACE_LISTEN  host:port the launcher listens on (default 127.0.0.1:5005;
                      0.0.0.0:5005 to accept other machines on the network).
"""

from __future__ import annotations

import json
import logging
import math
import os
import socket
from dataclasses import dataclass

from cuty.face.expressions import Expression

DEFAULT_ADDRESS = ("127.0.0.1", 5005)
MAX_DATAGRAM = 512
VERSION = 1


def parse_address(value: str | None, default: tuple[str, int] = DEFAULT_ADDRESS) -> tuple[str, int] | None:
    """Parse ``host:port``; ``None`` means disabled."""
    if value is None or not value.strip():
        return default
    value = value.strip()
    if value.lower() in {"off", "0", "false", "no", "none"}:
        return None
    host, sep, port = value.rpartition(":")
    if not sep:
        return value, default[1]
    try:
        number = int(port)
    except ValueError as exc:
        raise ValueError(f"Puerto inválido en {value!r}") from exc
    if not 0 <= number < 65536:
        raise ValueError(f"Puerto fuera de rango en {value!r}")
    return host or default[0], number


@dataclass(frozen=True)
class FaceMessage:
    type: str
    expression: str | None = None
    intensity: float = 1.0
    level: float = 0.0
    x: float = 0.5
    y: float = 0.5


def _unit(value) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("expected a number")
    if not 0 <= value <= 1:
        raise ValueError("expected 0..1")
    return float(value)


def decode(data: bytes) -> FaceMessage | None:
    """Validate a datagram; malformed or unknown messages return ``None``."""
    if len(data) > MAX_DATAGRAM:
        return None
    try:
        obj = json.loads(data.decode("utf-8"))
        if not isinstance(obj, dict) or obj.get("v") != VERSION:
            return None
        kind = obj.get("type")
        if kind == "expression":
            name = Expression(obj["expression"]).value
            return FaceMessage("expression", expression=name, intensity=_unit(obj.get("intensity", 1.0)))
        if kind == "mouth":
            return FaceMessage("mouth", level=_unit(obj["level"]))
        if kind == "look":
            return FaceMessage("look", x=_unit(obj["x"]), y=_unit(obj["y"]))
        if kind == "blink":
            return FaceMessage("blink")
    except (ValueError, KeyError, TypeError, UnicodeDecodeError):
        return None
    return None


class FaceLinkSender:
    def __init__(self, address: tuple[str, int] = DEFAULT_ADDRESS) -> None:
        self.address = address
        family = socket.AF_INET6 if ":" in address[0] else socket.AF_INET
        self._sock = socket.socket(family, socket.SOCK_DGRAM)
        self._sock.setblocking(False)

    @classmethod
    def from_env(cls) -> FaceLinkSender | None:
        address = parse_address(os.getenv("CUTY_FACE_LINK"))
        return cls(address) if address else None

    def _send(self, payload: dict) -> None:
        try:
            self._sock.sendto(json.dumps({"v": VERSION, **payload}, separators=(",", ":")).encode(), self.address)
        except OSError:
            pass  # Face not running, network down, buffer full: never break the voice.

    def expression(self, expression: Expression | str, intensity: float = 1.0) -> None:
        name = getattr(expression, "value", expression)
        self._send({"type": "expression", "expression": name, "intensity": round(float(intensity), 3)})

    def mouth(self, level: float) -> None:
        self._send({"type": "mouth", "level": round(min(1.0, max(0.0, level)), 3)})

    def look(self, x: float, y: float) -> None:
        self._send({"type": "look", "x": round(x, 3), "y": round(y, 3)})

    def blink(self) -> None:
        self._send({"type": "blink"})

    def close(self) -> None:
        self._sock.close()


class FaceLinkReceiver:
    """Non-blocking listener; put ``fileno()`` in a select() loop."""

    def __init__(self, address: tuple[str, int] = DEFAULT_ADDRESS) -> None:
        family = socket.AF_INET6 if ":" in address[0] else socket.AF_INET
        self._sock = socket.socket(family, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(address)
        self._sock.setblocking(False)
        self.address = self._sock.getsockname()[:2]

    @classmethod
    def from_env(cls) -> FaceLinkReceiver | None:
        try:
            address = parse_address(os.getenv("CUTY_FACE_LISTEN"))
            return cls(address) if address else None
        except (OSError, ValueError) as exc:
            logging.getLogger("CUTY FACE").warning("Sin enlace con la voz: %s", exc)
            return None

    def fileno(self) -> int:
        return self._sock.fileno()

    def poll(self, limit: int = 256) -> list[FaceMessage]:
        messages = []
        for _ in range(limit):
            try:
                data = self._sock.recv(MAX_DATAGRAM + 1)
            except (BlockingIOError, InterruptedError):
                break
            except OSError:
                break
            message = decode(data)
            if message is not None:
                messages.append(message)
        return messages

    def close(self) -> None:
        self._sock.close()
