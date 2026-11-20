"""Raspberry side of the V2 UART link to the STM32F401 FreeRTOS firmware.

The STM32 owns trajectories, limits, PWM and safety; the Pi only sends
high-level goals and must keep a heartbeat alive (>= 2 Hz; this bridge sends
10 Hz). Missing heartbeats for 500 ms latch FAULT on the STM32 and release the
servos. Wire format: see docs/protocol/protocol.md (V2 section).

Nothing here starts on import, and nothing moves unless the caller explicitly
calls ``arm()`` and ``start()`` and the firmware was built with ``make PWM=1``.

    python -m cuty.hardware.stm32_bridge --port /dev/serial0      # bench console
"""

from __future__ import annotations

import argparse
import math
import os
import threading
import time
from dataclasses import dataclass
from typing import BinaryIO, Callable, Optional, Union

JOINTS = ("HEAD_PAN", "LEFT_ARM", "RIGHT_ARM")
BAUD = 115200


@dataclass(frozen=True)
class Boot:
    reset: str
    clock: str
    sysclk_hz: int
    build: str  # "DRYRUN" or "PWM"


@dataclass(frozen=True)
class Reply:
    sequence: int
    accepted: bool
    command: str
    joint: Optional[str] = None


@dataclass(frozen=True)
class Telemetry:
    timestamp_ms: int
    state: str          # DISARMED, READY, ACTIVE, FAULT
    fault: str          # NONE, INVALID, RX, STALE, HEARTBEAT, OVERRUN, LIMIT, BATTERY
    output_enabled: bool
    head_pan: float     # commanded, normalized -1..1 (not measured)
    left_arm: float
    right_arm: float
    battery_v: float    # 0.0 = no pack measured
    rx_errors: int
    dropped: int


@dataclass(frozen=True)
class Diag:
    timestamp_ms: int
    stack_free: dict
    heap_min_free: int
    rx_overflows: int
    tx_overflows: int


Record = Union[Boot, Reply, Telemetry, Diag]


def parse_record(line: str) -> Optional[Record]:
    """Parse one STM32 -> Pi line; returns None for anything unknown or malformed."""
    f = line.strip().split(",")
    try:
        if len(f) == 6 and f[:2] == ["V2", "BOOT"]:
            return Boot(f[2], f[3], int(f[4]), f[5])
        if len(f) in (4, 5) and f[0] == "V2" and f[1] in ("ACK", "NAK"):
            return Reply(int(f[2]), f[1] == "ACK", f[3], f[4] if len(f) == 5 else None)
        if len(f) == 12 and f[:2] == ["V2", "TEL"]:
            return Telemetry(int(f[2]), f[3], f[4], f[5] == "1", int(f[6]) / 1000, int(f[7]) / 1000,
                             int(f[8]) / 1000, int(f[9]) / 1000, int(f[10]), int(f[11]))
        if len(f) == 11 and f[:2] == ["V2", "DIAG"]:
            names = ("CommunicationTask", "ServoControlTask", "SafetyTask", "DiagnosticsTask", "TxTask")
            return Diag(int(f[2]), dict(zip(names, map(int, f[3:8]))), int(f[8]), int(f[9]), int(f[10]))
    except ValueError:
        return None
    return None


def format_target(joint: str, value: float) -> str:
    """V2,TARGET line for a normalized goal in -1..1 (milli-units on the wire)."""
    if joint not in JOINTS:
        raise ValueError(f"joint must be one of {JOINTS}")
    if not math.isfinite(value) or not -1.0 <= value <= 1.0:
        raise ValueError("target must be a finite value in -1..1")
    return f"V2,TARGET,{joint},{round(value * 1000)}"


class Stm32Bridge:
    """Line-oriented link: a reader thread parses records, a heartbeat thread keeps the STM32 alive."""

    def __init__(self, reader: BinaryIO, writer: BinaryIO, heartbeat_period: float = 0.1,
                 on_record: Optional[Callable[[Record], None]] = None) -> None:
        self._reader, self._writer = reader, writer
        self._period = heartbeat_period
        self._on_record = on_record
        self._lock = threading.Condition()
        self._write_lock = threading.Lock()
        self._running = False
        self._heartbeat = True
        self.boot: Optional[Boot] = None
        self.telemetry: Optional[Telemetry] = None
        self.diag: Optional[Diag] = None
        self.replies: list[Reply] = []

    # -- lifecycle -----------------------------------------------------
    def start(self) -> "Stm32Bridge":
        self._running = True
        threading.Thread(target=self._read_loop, name="stm32-rx", daemon=True).start()
        threading.Thread(target=self._heartbeat_loop, name="stm32-hb", daemon=True).start()
        return self

    def stop_heartbeat(self) -> None:
        """Keep reading but stop HB: the STM32 latches FAULT,HEARTBEAT within 0.5 s."""
        self._heartbeat = False

    def close(self) -> None:
        """Stops both threads; without heartbeat the STM32 faults and releases the servos."""
        self._heartbeat = False
        self._running = False

    # -- commands ------------------------------------------------------
    def send(self, line: str) -> None:
        with self._write_lock:
            self._writer.write((line + "\n").encode("ascii"))
            self._writer.flush()

    def arm(self) -> None: self.send("V2,ARM")
    def start_motion(self) -> None: self.send("V2,START")
    def disarm(self) -> None: self.send("V2,DISARM")
    def reset(self) -> None: self.send("V2,RESET")

    def set_target(self, joint: str, value: float) -> None:
        self.send(format_target(joint, value))

    def wait_for(self, predicate: Callable[["Stm32Bridge"], bool], timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        with self._lock:
            while not predicate(self):
                left = deadline - time.monotonic()
                if left <= 0:
                    return False
                self._lock.wait(left)
        return True

    def wait_state(self, state: str, timeout: float = 2.0) -> bool:
        return self.wait_for(lambda b: b.telemetry is not None and b.telemetry.state == state, timeout)

    # -- threads -------------------------------------------------------
    def _heartbeat_loop(self) -> None:
        while self._running and self._heartbeat:
            try:
                self.send("V2,HB")
            except (OSError, ValueError):
                self._running = False
                break
            time.sleep(self._period)

    def _read_loop(self) -> None:
        pending = b""
        while self._running:
            try:
                chunk = self._reader.read1(256) if hasattr(self._reader, "read1") else self._reader.read(1)
            except (OSError, ValueError):
                break
            if not chunk:
                break
            pending += chunk
            while b"\n" in pending:
                raw, pending = pending.split(b"\n", 1)
                record = parse_record(raw.decode("ascii", "replace"))
                if record is None:
                    continue
                with self._lock:
                    if isinstance(record, Boot):
                        self.boot = record
                    elif isinstance(record, Telemetry):
                        self.telemetry = record
                    elif isinstance(record, Diag):
                        self.diag = record
                    else:
                        self.replies = (self.replies + [record])[-64:]
                    self._lock.notify_all()
                if self._on_record:
                    self._on_record(record)
        self._running = False


def open_serial(path: str = "/dev/serial0", baud: int = BAUD) -> tuple[BinaryIO, BinaryIO]:
    """Raw 115200 8N1 port using only the standard library (Linux/macOS)."""
    import termios

    fd = os.open(path, os.O_RDWR | os.O_NOCTTY)
    attrs = termios.tcgetattr(fd)
    speed = getattr(termios, f"B{baud}")
    attrs[0] = 0                                   # iflag: raw
    attrs[1] = 0                                   # oflag: raw
    attrs[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
    attrs[3] = 0                                   # lflag: no echo, non-canonical
    attrs[4] = attrs[5] = speed
    attrs[6][termios.VMIN] = 1
    attrs[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    termios.tcflush(fd, termios.TCIOFLUSH)
    return os.fdopen(fd, "rb", buffering=0), os.fdopen(os.dup(fd), "wb", buffering=0)


def _console(bridge: Stm32Bridge) -> None:
    help_text = ("commands: arm | start | disarm | reset | pan X | left X | right X | status | quit"
                 "  (X in -1..1)")
    print(help_text)
    aliases = {"pan": "HEAD_PAN", "left": "LEFT_ARM", "right": "RIGHT_ARM"}
    while True:
        try:
            words = input("cuty> ").split()
        except EOFError:
            break
        if not words:
            continue
        cmd = words[0].lower()
        try:
            if cmd == "quit":
                break
            elif cmd == "arm":
                bridge.arm()
            elif cmd == "start":
                bridge.start_motion()
            elif cmd == "disarm":
                bridge.disarm()
            elif cmd == "reset":
                bridge.reset()
            elif cmd in aliases and len(words) == 2:
                bridge.set_target(aliases[cmd], float(words[1]))
            elif cmd == "status":
                print(bridge.boot, bridge.telemetry, bridge.diag, sep="\n")
            else:
                print(help_text)
        except ValueError as exc:
            print(f"error: {exc}")
    bridge.close()


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Bench console for the C.U.T.Y STM32 firmware")
    parser.add_argument("--port", default="/dev/serial0", help="serial device (Pi GPIO14/15 UART)")
    args = parser.parse_args(argv)
    reader, writer = open_serial(args.port)
    bridge = Stm32Bridge(reader, writer, on_record=lambda r: print(f"  {r}") if not isinstance(r, Telemetry) else None)
    _console(bridge.start())


if __name__ == "__main__":
    main()
