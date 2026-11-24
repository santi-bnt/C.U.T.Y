"""Prueba manual V2 para firmware compilado con --bench-channel; solo servo suelto."""
import argparse
import math
import time

from .robot_commands import command, parse_response, target
from .stm32_bridge import STM32Bridge

CHANNEL_AXES = {1: "HEAD_PAN", 2: "LEFT_ARM", 3: "RIGHT_ARM"}


def require_ack(bridge, wire):
    reply = bridge.exchange(wire, timeout=0.3)
    print(reply)
    parsed = parse_response(reply)
    if not parsed.accepted:
        raise RuntimeError(f"STM32 rechazo la prueba: {reply}")
    return parsed


def run_test(bridge, channel, milli_units, seconds):
    """Mantiene una sola sesión y HB; el llamador debe cerrar/desarmar al salir."""
    if channel not in CHANNEL_AXES or not -1000 <= milli_units <= 1000:
        raise ValueError("Canal o consigna fuera de rango")
    if not math.isfinite(seconds) or not 0 < seconds <= 10:
        raise ValueError("La prueba debe durar mas de 0 y hasta 10 segundos")
    response = require_ack(bridge, command("V2,HB"))
    if response.fields[-1] == "FAULT":
        require_ack(bridge, command("V2,RESET"))
    require_ack(bridge, command("V2,DISARM"))
    require_ack(bridge, command("V2,HB"))
    require_ack(bridge, command("V2,ARM"))
    require_ack(bridge, command("V2,START"))
    require_ack(bridge, target(CHANNEL_AXES[channel], milli_units))
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        response = require_ack(bridge, command("V2,HB"))
        if response.fields[-1] != "ACTIVE":
            raise RuntimeError("STM32 salio de ACTIVE durante la prueba")
        time.sleep(0.1)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True)
    parser.add_argument("--channel", required=True, type=int, choices=(1, 2, 3),
                        help="Debe coincidir con el canal seleccionado al compilar")
    parser.add_argument("--target", required=True, type=int,
                        help="-1000..1000: 1400..1600 us en firmware de banco")
    parser.add_argument("--seconds", type=float, default=3)
    args = parser.parse_args(argv)
    if not -1000 <= args.target <= 1000:
        parser.error("--target debe estar entre -1000 y 1000")
    if not math.isfinite(args.seconds) or not 0 < args.seconds <= 10:
        parser.error("--seconds debe estar entre mas de 0 y 10")
    try:
        bridge = STM32Bridge(args.port)
        try:
            run_test(bridge, args.channel, args.target, args.seconds)
        finally:
            # También desarma ante NACK, timeout o Ctrl+C; no corta alimentación.
            bridge.close()
    except KeyboardInterrupt:
        print("Prueba interrumpida; se intento desarmar.")
        return 130
    except (OSError, RuntimeError, ConnectionError, ValueError) as exc:
        print(f"Error: {exc}")
        return 2
    print("Prueba terminada; PWM desarmado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
