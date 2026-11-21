"""Compila y ejecuta la simulacion C con un GCC de escritorio (no el de ARM)."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--cc", default=os.environ.get("CC", "gcc"))
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="cuty-uart-") as directory:
    binary = Path(directory) / ("test.exe" if os.name == "nt" else "test")
    subprocess.run([args.cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-I" + str(root / "tests/fakes"), "-I" + str(root / "Core/Inc"),
                    str(root / "tests/test_servo_uart.c"),
                    str(root / "Core/Src/servo_command.c"), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
