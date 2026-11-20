"""Compile and execute the portable C core; never builds or flashes STM32."""
from pathlib import Path
import os
import shlex
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
compiler_setting = os.environ.get("CC", "cc")
compiler = [compiler_setting] if Path(compiler_setting).is_file() else shlex.split(compiler_setting)
sources = ["App/communication/uart_protocol.c", "App/communication/wire.c",
           "App/control/body_control.c", "App/control/fir_filter.c",
           "App/power/battery.c", "App/supervision/liveness.c",
           "App/safety/safety.c", "App/servos/servo.c", "App/servos/calibration.c"]
with tempfile.TemporaryDirectory(prefix="cuty-motion-") as directory:
    executable = Path(directory) / ("motion-test.exe" if os.name == "nt" else "motion-test")
    for test in ["tests/test_motion.c", "tests/test_rtos.c", "tests/test_firmware_core.c"]:
        subprocess.run(compiler + ["-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                       "-DCUTY_RTOS_DRY_RUN=1", "-I", str(root / "tests/fakes")] +
                       [str(root / source) for source in sources + [test]] +
                       ([] if os.name == "nt" else ["-lm"]) + ["-o", str(executable)], check=True)
        subprocess.run([str(executable)], check=True)
