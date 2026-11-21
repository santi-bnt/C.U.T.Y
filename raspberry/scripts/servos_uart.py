"""Prueba sencilla de un servo de la Black Pill por UART (no controla GPIO PWM)."""
import argparse
import math
import time


def send_command(port, command):
    """Cada envio termina en LF y debe tener su respuesta antes del siguiente."""
    port.write((command + "\n").encode("ascii"))
    response = port.readline().decode("ascii", errors="replace").strip()
    expected = "OK " + command.split(",", 1)[0]
    if response != expected:
        raise RuntimeError(f"{command}: {response or 'sin respuesta de la Black Pill'}")


def run_test(port, servo, pulse_us, seconds):
    # STOP tambien libera un bloqueo por perdida previa de comunicacion.
    # La linea vacia sincroniza el receptor si quedo un comando a medias.
    port.reset_input_buffer()
    port.write(b"\n")
    time.sleep(0.05)
    port.reset_input_buffer()
    try:
        send_command(port, "STOP")
        send_command(port, "PING")
        if servo is None:
            print("UART responde. Los tres PWM estan apagados.")
            return
        send_command(port, f"SERVO,{servo},{pulse_us}")
        print(f"Servo {servo}: pulso de {pulse_us} us durante {seconds:g} segundos.")
        end = time.monotonic() + seconds
        # El PING evita el apagado por ausencia de comunicacion (2 segundos).
        while time.monotonic() < end:
            time.sleep(min(0.5, max(0, end - time.monotonic())))
            send_command(port, "PING")
    finally:
        # Al terminar o pulsar Ctrl+C apagamos TODOS los canales.
        # Si el cable se desconecto, lo hara el timeout de la Black Pill.
        send_command(port, "STOP")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="UART de GPIO14/15; confirmar ruta en la Pi")
    parser.add_argument("--servo", type=int, choices=(1, 2, 3),
                        help="1=cabeza PB6, 2=brazo izquierdo PB7, 3=brazo derecho PB8; sin esta opcion solo comprueba UART")
    parser.add_argument("--us", type=int, default=1500, help="Pulso de 1000 a 2000 us (predeterminado: 1500)")
    parser.add_argument("--seconds", type=float, default=3, help="Tiempo de prueba; predeterminado: 3 s")
    args = parser.parse_args()
    if not 1000 <= args.us <= 2000:
        parser.error("--us debe estar entre 1000 y 2000")
    if not math.isfinite(args.seconds) or not 0 < args.seconds <= 60:
        parser.error("--seconds debe estar entre mas de 0 y 60")
    try:
        import serial
    except ImportError:
        parser.exit(1, "Falta pyserial. Instala con: python -m pip install pyserial\n")
    try:
        # 115200, 8N1. Un solo programa debe ser dueno de este puerto.
        with serial.Serial(args.port, 115200, timeout=1, write_timeout=1,
                           exclusive=True) as port:
            run_test(port, args.servo, args.us, args.seconds)
    except KeyboardInterrupt:
        print("Prueba interrumpida.")
    except (OSError, RuntimeError, serial.SerialException) as exc:
        parser.exit(1, f"Error UART: {exc}\n")


if __name__ == "__main__":
    main()
