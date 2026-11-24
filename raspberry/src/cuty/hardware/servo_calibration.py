"""Calibración manual V2: un solo eje, sin barridos ni seguimiento automático."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import select
import sys
import time

from .robot_commands import Axis, command, parse_response
from .stm32_bridge import STM32Bridge

PINS = {"HEAD_PAN": "PB6/J7", "LEFT_ARM": "PB7/J8", "RIGHT_ARM": "PB8/J9"}


class CalibrationSession:
    """Una sola hebra es dueña de UART y mantiene HB mientras espera al usuario."""

    def __init__(self, bridge, axis):
        self.bridge = bridge
        self.axis = Axis(axis).value
        self.pulse_us = 1500
        self.sequence = None

    def exchange(self, line, expected_state=None):
        reply = parse_response(self.bridge.exchange(command(line), timeout=0.2))
        if reply.kind != "ACK" or len(reply.fields) != 3:
            # ACK: V2,ACK,secuencia,OK,estado (tres campos tras el tipo).
            raise RuntimeError(f"Orden rechazada o respuesta inesperada: {reply}")
        sequence, result, state = reply.fields
        if not sequence.isascii() or not sequence.isdigit() or result != "OK":
            raise RuntimeError(f"ACK inválido: {reply}")
        number = int(sequence)
        if self.sequence is not None and number != self.sequence + 1:
            raise RuntimeError("La secuencia UART no coincide; se detiene la prueba.")
        self.sequence = number
        if expected_state is not None and state != expected_state:
            raise RuntimeError(f"Estado {state}; se esperaba {expected_state}.")
        return state

    def start(self, reset_fault=False):
        # Vaciar solo al abrir: nunca descartar respuestas de una orden pendiente.
        self.bridge.serial.reset_input_buffer()
        self.bridge._rx_buffer.clear()
        state = self.exchange("V2,DISARM")
        if state == "FAULT":
            if not reset_fault:
                raise RuntimeError("El controlador está en FAULT. Revisa la causa y repite con --reset-fault.")
            self.exchange("V2,RESET", "DISARMED")
        elif state != "DISARMED":
            raise RuntimeError(f"Estado inicial inesperado: {state}")
        self.exchange("V2,HB", "DISARMED")
        self.exchange("V2,ARM", "READY")
        self.exchange(f"V2,CAL,{self.axis},1500", "READY")

    def step(self, direction):
        pulse = self.pulse_us + direction * 10
        if not 1000 <= pulse <= 2000:
            raise ValueError("Límite de esta prueba: 1000–2000 us.")
        self.exchange(f"V2,CAL,{self.axis},{pulse}", "READY")
        self.pulse_us = pulse


def read_control(timeout):
    # En Linux, select espera una línea de terminal sin bloquear el heartbeat.
    readable, _, _ = select.select([sys.stdin], [], [], timeout)
    if not readable:
        return None
    line = sys.stdin.readline()
    return line.strip().lower() if line else "q"


def run_session(session, seconds, read=read_control):
    points = {}
    reverse = None
    started = time.monotonic()
    last_step = started
    next_heartbeat = started
    print(f"{session.axis} ({PINS[session.axis]}): 1500 us, referencia sin calibrar.")
    print("Escribe y pulsa Enter: + / - (10 us), min, centro, max, invertir, q (apagar).")
    while time.monotonic() - started < seconds:
        now = time.monotonic()
        if now >= next_heartbeat:
            session.exchange("V2,HB", "READY")
            next_heartbeat = time.monotonic() + 0.1
        control = read(0.05)
        if control == "q":
            break
        if control in {"+", "-"}:
            if time.monotonic() - last_step < 0.12:
                print("Espera un instante antes del siguiente paso.")
                continue
            if not 1000 <= session.pulse_us + (10 if control == "+" else -10) <= 2000:
                print("Se alcanzó el límite de la ventana de prueba.")
                continue
            session.step(1 if control == "+" else -1)
            last_step = time.monotonic()
            print(f"Pulso solicitado: {session.pulse_us} us")
        elif control in {"min", "centro", "max"}:
            key = {"min": "min_us", "centro": "center_us", "max": "max_us"}[control]
            points[key] = session.pulse_us
            print(f"Anotado {key} = {session.pulse_us}; es una observación, no validación automática.")
        elif control == "invertir":
            reverse = not reverse
            print(f"Sentido invertido anotado: {reverse}")
        elif control:
            print("Usa +, -, min, centro, max, invertir o q.")
    return {"axis": session.axis, "pin": PINS[session.axis], "observed_points": points,
            "reverse": reverse, "mechanical_calibration_confirmed": False,
            "note": "Pulsos solicitados; no hay medición de posición ni detección de topes."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True)
    parser.add_argument("--axis", required=True, choices=[axis.value for axis in Axis])
    parser.add_argument("--seconds", type=int, default=45, choices=range(1, 56), metavar="1..55")
    parser.add_argument("--confirm-unloaded", action="store_true",
                        help="Confirma que el eje puede ir a 1500 us sin forzar el mecanismo")
    parser.add_argument("--reset-fault", action="store_true", help="Permite RESET explícito al iniciar")
    parser.add_argument("--output", type=Path, help="JSON nuevo donde guardar las observaciones")
    args = parser.parse_args(argv)
    if not args.confirm_unloaded:
        parser.error("Descarga el mecanismo y usa --confirm-unloaded: la primera orden será de 1500 us.")
    if os.name != "posix" or not sys.stdin.isatty():
        parser.error("Ejecuta esta prueba en una terminal interactiva de la Raspberry.")
    output = args.output or Path(f"servo-calibration-{args.axis}.json")
    if output.exists():
        parser.error(f"Ya existe {output}; indica otro --output para conservar esa medición.")
    bridge = None
    try:
        bridge = STM32Bridge(args.port)
        session = CalibrationSession(bridge, args.axis)
        session.start(args.reset_fault)
        try:
            result = run_session(session, args.seconds)
        finally:
            # Primero se apaga el canal; escribir el JSON nunca prolonga el movimiento.
            session.exchange("V2,DISARM")
        with output.open("x", encoding="utf-8") as file:
            json.dump(result, file, ensure_ascii=False, indent=2)
            file.write("\n")
        print(f"PWM apagado. Observaciones guardadas en {output}.")
        return 0
    except KeyboardInterrupt:
        print("Prueba interrumpida; se solicita DISARM.")
        return 130
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Calibración detenida: {exc}", file=sys.stderr)
        return 1
    finally:
        if bridge is not None:
            bridge.close()


if __name__ == "__main__":
    raise SystemExit(main())
