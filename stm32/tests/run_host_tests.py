"""Compile and execute the portable C core; never builds or flashes STM32."""
from pathlib import Path
import os
import shlex
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
compiler_setting = os.environ.get("CC", "cc")
compiler = [compiler_setting] if Path(compiler_setting).is_file() else shlex.split(compiler_setting)
sources = ["App/communication/uart_protocol.c", "App/control/body_control.c",
           "App/control/fir_filter.c",
           "App/control/manual_calibration.c",
           "App/safety/safety.c", "App/servos/servo.c"]
with tempfile.TemporaryDirectory(prefix="cuty-motion-") as directory:
    executable = Path(directory) / ("motion-test.exe" if os.name == "nt" else "motion-test")
    for test, extra in [("tests/test_motion.c", []), ("tests/test_rtos.c", []),
                        ("tests/test_calibration.c", []),
                        ("tests/test_rtos.c", ["-DCUTY_TEST_CALIBRATION=1"])]:
        subprocess.run(compiler + ["-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                       "-DCUTY_RTOS_DRY_RUN=1", "-I", str(root / "tests/fakes")] + extra +
                       [str(root / source) for source in sources + [test]] +
                       ([] if os.name == "nt" else ["-lm"]) + ["-o", str(executable)], check=True)
        subprocess.run([str(executable)], check=True)
    for calibration in (0, 1):
        subprocess.run(compiler + ["-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                       f"-DCUTY_CALIBRATION_ENABLE={calibration}", "-I", str(root / "tests/board_fakes"),
                       str(root / "Board/cuty_servo_output.c"), str(root / "App/servos/servo.c"),
                       str(root / "tests/test_calibration_output.c"),
                       "-o", str(executable)] + ([] if os.name == "nt" else ["-lm"]), check=True)
        subprocess.run([str(executable)], check=True)
