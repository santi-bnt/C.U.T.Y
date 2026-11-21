"""Prueba los comandos y el apagado sin abrir un puerto real."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "servos_uart", Path(__file__).resolve().parents[1] / "scripts/servos_uart.py")
client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)


class FakePort:
    def __init__(self, error=None):
        self.sent = []
        self.command = ""
        self.error = error

    def reset_input_buffer(self):
        pass

    def write(self, data):
        self.command = data.decode("ascii").strip()
        self.sent.append(self.command)

    def readline(self):
        if self.command.startswith("SERVO") and self.error is not None:
            return self.error
        return ("OK " + self.command.split(",")[0] + "\n").encode("ascii")


class ClientTests(unittest.TestCase):
    @patch.object(client.time, "sleep")
    def test_check_does_not_move_servos(self, sleep):
        port = FakePort()
        client.run_test(port, None, 1500, 3)
        self.assertEqual(port.sent, ["", "STOP", "PING", "STOP"])

    @patch.object(client.time, "sleep")
    @patch.object(client.time, "monotonic", side_effect=[0, 0, 0, 4])
    def test_movement_has_heartbeat_and_stop(self, monotonic, sleep):
        port = FakePort()
        client.run_test(port, 2, 1500, 3)
        self.assertEqual(port.sent, ["", "STOP", "PING", "SERVO,2,1500", "PING", "STOP"])

    @patch.object(client.time, "sleep")
    def test_bad_or_missing_reply_stops(self, sleep):
        for response in (b"ERR COMMAND\n", b"", b"OK PING\n"):
            port = FakePort(response)
            with self.assertRaises(RuntimeError):
                client.run_test(port, 1, 1500, 3)
            self.assertEqual(port.sent[-1], "STOP")
            self.assertEqual(port.sent.count("SERVO,1,1500"), 1)

    @patch.object(client.time, "sleep")
    @patch.object(client.time, "monotonic", side_effect=KeyboardInterrupt)
    def test_ctrl_c_stops(self, monotonic, sleep):
        port = FakePort()
        with self.assertRaises(KeyboardInterrupt):
            client.run_test(port, 1, 1500, 3)
        self.assertEqual(port.sent[-1], "STOP")


if __name__ == "__main__":
    unittest.main()
