"""Opt-in diagnostic UART bridge. It never arms or starts the controller automatically."""
from __future__ import annotations

import argparse
from collections import deque
import os
import sys
import time
from pathlib import Path
from typing import Any

from .robot_commands import Axis, command, parse_response, target

try:
    import fcntl
except ImportError:  # host-side tests on Windows; Raspberry Pi uses flock
    fcntl = None
    import msvcrt


class STM32Bridge:
    """Propietario exclusivo de un UART; no arma el controlador al abrirlo."""

    def __init__(self, port: str, baudrate: int = 115200, serial_factory: Any = None):
        self.port = port
        self._rx_buffer = bytearray()
        # El STM32 puede emitir TELEM cada 10 ms; conservar solo un lote acotado.
        self.events = deque(maxlen=64)
        self._lock_file = None
        # El lock se toma antes de abrir pyserial para evitar dos propietarios simultáneos.
        try:
            lock_path = Path("/run/lock") / ("cuty-stm32-" + Path(port).name.replace("/", "_") + ".lock")
            self._lock_file = open(lock_path, "w")
            if fcntl is not None:
                fcntl.flock(self._lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            else:
                self._lock_file.write("0")
                self._lock_file.flush()
                self._lock_file.seek(0)
                msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        except (OSError, BlockingIOError):
            raise RuntimeError(f"UART {port} is already controlled by another C.U.T.Y process")
        try:
            if serial_factory is None:
                import serial
                serial_factory = serial.Serial
            # En Linux también evita que otro programa abra el mismo dispositivo.
            options = {"exclusive": True} if fcntl is not None else {}
            self.serial = serial_factory(port, baudrate=baudrate, timeout=0.1, write_timeout=1, **options)
        except Exception:
            self._release_lock()
            raise

    def _release_lock(self) -> None:
        if self._lock_file:
            if fcntl is not None:
                fcntl.flock(self._lock_file, fcntl.LOCK_UN)
            else:
                self._lock_file.seek(0)
                msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            self._lock_file.close()
            self._lock_file = None

    def close(self) -> None:
        """Intenta DISARM antes de cerrar; si el enlace cayó, el STM32 aplica su timeout."""
        try:
            try:
                self.exchange(command("V2,DISARM"), timeout=0.25)
            except (OSError, ConnectionError, TimeoutError, ValueError):
                pass
        finally:
            try:
                self.serial.close()
            finally:
                self._release_lock()

    def exchange(self, wire: bytes, timeout: float = 1.0) -> str:
        """Envía una línea y espera ACK/NACK, guardando STATE/TELEM asíncronos."""
        try:
            self.serial.write(wire)
            self.serial.flush()
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                chunk = self.serial.readline()
                if chunk:
                    self._rx_buffer.extend(chunk)
                    while b"\n" in self._rx_buffer:
                        raw, _, remaining = self._rx_buffer.partition(b"\n")
                        self._rx_buffer = bytearray(remaining)
                        line = raw.decode("ascii", errors="replace").strip()
                        parsed = parse_response(line)
                        # STATE/TELEM pueden llegar antes de ACK; se conservan y se sigue leyendo.
                        if parsed.kind in {"ACK", "NACK"}:
                            return line
                        self.events.append(parsed)
            raise TimeoutError("STM32 did not return a line before timeout")
        except (OSError, TimeoutError) as exc:
            raise ConnectionError(f"UART {self.port}: {exc}") from exc

    def drain_events(self) -> tuple:
        """Retira STATE/TELEM asíncronos sin permitir crecimiento ilimitado."""
        events = tuple(self.events)
        self.events.clear()
        return events

    def heartbeat(self, interval: float = 0.25, count: int = 1) -> None:
        """Envía HB a intervalos menores que el timeout del controlador."""
        for _ in range(count):
            print(self.exchange(command("V2,HB")))
            if count > 1:
                time.sleep(interval)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", default=os.getenv("CUTY_STM32_PORT"), help="serial device (or CUTY_STM32_PORT)")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--timeout", type=float, default=1.0)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("status", help="send a heartbeat and inspect the reply")
    sub.add_parser("heartbeat", help="send heartbeat continuously until Ctrl-C")
    send = sub.add_parser("send", help="send one explicit V2 command")
    send.add_argument("command")
    move = sub.add_parser("target", help="validate and transmit a software target (no PWM in stage 1)")
    move.add_argument("axis", choices=[a.value for a in Axis])
    move.add_argument("milli_units", type=int)
    args = parser.parse_args(argv)
    if not args.port:
        parser.error("set --port or CUTY_STM32_PORT; device names vary across Raspberry Pi installations")
    try:
        bridge = STM32Bridge(args.port, args.baud)
        try:
            if args.action == "status":
                print(bridge.exchange(command("V2,HB"), args.timeout))
                print(bridge.exchange(command("V2,INFO"), args.timeout))
            elif args.action == "heartbeat":
                while True:
                    try:
                        print(bridge.exchange(command("V2,HB"), args.timeout))
                    except ConnectionError:
                        bridge.close()
                        time.sleep(1.0)
                        bridge = STM32Bridge(args.port, args.baud)
                    time.sleep(0.25)
            elif args.action == "send":
                print(bridge.exchange(command(args.command), args.timeout))
            else:
                print(bridge.exchange(target(args.axis, args.milli_units), args.timeout))
        finally:
            bridge.close()
    except (OSError, RuntimeError, ConnectionError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
