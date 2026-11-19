"""Compile application objects only; no board startup, link, image or flash."""
import argparse
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--cc", required=True, help="Path to arm-none-eabi-gcc")
parser.add_argument("--cmsis", required=True, help="Directory containing genuine cmsis_os2.h")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
sources = ["App/communication/uart_protocol.c", "App/control/body_control.c",
           "App/control/fir_filter.c",
           "App/safety/safety.c", "App/servos/servo.c", "App/rtos/motion_tasks.c"]
subprocess.run([args.cc, "--version"], check=True)
with tempfile.TemporaryDirectory(prefix="cuty-arm-objects-") as directory:
    for source in sources:
        output = Path(directory) / (Path(source).stem + ".o")
        subprocess.run([args.cc, "-mcpu=cortex-m4", "-mthumb", "-mfloat-abi=soft",
                        "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                        "-DCUTY_RTOS_DRY_RUN=1", "-I", args.cmsis, "-c",
                        str(root / source), "-o", str(output)], check=True)
        print("ARM object compiled:", source)
print("PASS: application objects only; no STM32 firmware image linked or executed")
