"""Compila el firmware con GCC para ARM. No descarga herramientas ni graba la placa."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cc", help="Ruta a arm-none-eabi-gcc, si no esta en PATH")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--bench-channel", type=int, choices=(1, 2, 3),
                      help="PWM de banco en un canal: 1=J7/PB6, 2=J8/PB7, 3=J9/PB8")
    mode.add_argument("--calibration", action="store_true",
                      help="Genera firmware separado para calibración manual de un servo")
    mode.add_argument("--profile", type=Path,
                      help="Perfil JSON confirmado para habilitar los tres ejes físicos")
    args = parser.parse_args()
    cc = args.cc or shutil.which("arm-none-eabi-gcc")
    if not cc:
        # En Windows tambien aprovechamos el compilador instalado con CubeIDE.
        installed = sorted(Path("C:/ST").glob(
            "STM32CubeIDE*/STM32CubeIDE/plugins/"
            "com.st.stm32cube.ide.mcu.externaltools.gnu-tools*/tools/bin/arm-none-eabi-gcc.exe"
        ))
        cc = str(installed[-1]) if installed else None
    if not cc:
        parser.error("Instala STM32CubeIDE o indica --cc RUTA/arm-none-eabi-gcc")

    root = Path(__file__).resolve().parent
    output = root / "build"
    if args.bench_channel:
        output = output / f"bench-j{args.bench_channel + 6}"
    if args.calibration:
        output = output / "calibration"
    if args.profile:
        output = output / "physical"
    output.mkdir(parents=True, exist_ok=True)
    rtos = root / "Middlewares/Third_Party/FreeRTOS/Source"
    includes = ["Core/Inc", "Drivers/STM32F4xx_HAL_Driver/Inc",
                "Drivers/CMSIS/Include", "Drivers/CMSIS/Device/ST/STM32F4xx/Include",
                str(rtos / "include"), str(rtos / "CMSIS_RTOS_V2"),
                str(rtos / "portable/GCC/ARM_CM4F")]
    sources = sorted(root.glob("Core/Src/*.c"))
    sources += sorted(root.glob("Drivers/STM32F4xx_HAL_Driver/Src/*.c"))
    sources += sorted(rtos.glob("*.c"))
    sources += [rtos / "CMSIS_RTOS_V2/cmsis_os2.c",
                rtos / "portable/GCC/ARM_CM4F/port.c",
                rtos / "portable/MemMang/heap_4.c",
                root / "Core/Startup/startup_stm32f401ccux.s"]
    # El proyecto compila el mismo parser, controlador y tareas que prueban los tests host.
    sources += sorted((root.parent / "App").rglob("*.c"))
    sources += sorted((root.parent / "Board").glob("*.c"))
    if args.profile:
        sys.path.insert(0, str(root.parents[1] / "raspberry" / "src"))
        from cuty.hardware.calibration_profile import RobotCalibration
        profile = RobotCalibration.load(args.profile)
        profile_header = output / "servo_calibration_profile.h"
        lines = ["#ifndef CUTY_SERVO_CALIBRATION_PROFILE_H", "#define CUTY_SERVO_CALIBRATION_PROFILE_H",
                 '#include "cuty_servo_output.h"', "/* Generado desde un perfil validado por eje. */"]
        axes = {axis.axis: axis for axis in profile.axes}
        lines.append("static const CutyServoTestRange cuty_servo_test_ranges[3] = {")
        for axis_name in ("HEAD_PAN", "LEFT_ARM", "RIGHT_ARM"):
            axis = axes[axis_name]
            lines.append(f"    {{{axis.min_us}U, {axis.max_us}U}},")
        lines.append("};")
        lines.append("static const CutyServoCalibration cuty_servo_calibration[3] = {")
        for index, axis_name in enumerate(("HEAD_PAN", "LEFT_ARM", "RIGHT_ARM"), 1):
            axis = axes[axis_name]
            reverse = "true" if axis.reverse else "false"
            lines.append(
                f"    {{{axis.min_us}U, {axis.center_us}U, {axis.max_us}U, "
                f"{axis.max_velocity_per_s:.9g}f, {axis.max_acceleration_per_s2:.9g}f, "
                f"{reverse}, true, true, {index}U}},")
        lines += ["};", "#endif", ""]
        profile_header.write_text("\n".join(lines), encoding="ascii")
    name = ("cuty_arms_pwm_blackpill_physical" if args.profile else
            "cuty_arms_pwm_blackpill_calibration" if args.calibration else "cuty_arms_pwm_blackpill")
    elf = output / (name + ".elf")
    # Una sola orden mantiene este ejemplo facil de leer y de reproducir.
    command = [cc, "-mcpu=cortex-m4", "-mthumb", "-mfpu=fpv4-sp-d16",
               "-mfloat-abi=hard", "-std=gnu11", "-Og", "-g3", "-Wall", "-Wextra",
               "-ffunction-sections", "-fdata-sections", "-DUSE_HAL_DRIVER",
               "-DSTM32F401xC", "--specs=nano.specs", "--specs=nosys.specs"]
    command += ["-I" + str(root / include) for include in includes]
    if args.profile:
        command += ["-I" + str(output), "-DCUTY_PHYSICAL_OUTPUT_ENABLE=1"]
    if args.bench_channel:
        command += [f"-DCUTY_BENCH_CHANNEL={args.bench_channel}"]
    if args.calibration:
        command += ["-DCUTY_CALIBRATION_ENABLE=1"]
    command += ["-I" + str(root.parent / "App"), "-I" + str(root.parent / "Board")]
    command += [str(source) for source in sources]
    command += ["-T" + str(root / "STM32F401CCUX_FLASH.ld"),
                "-Wl,--gc-sections", "-Wl,-Map=" + str(output / "firmware.map"),
                "-Wl,--print-memory-usage", "-o", str(elf), "-lm", "-lc"]
    subprocess.run(command, check=True)
    # El .bin sirve para STM32CubeProgrammer; el .elf incluye simbolos de depuracion.
    suffix = ".exe" if str(cc).endswith(".exe") else ""
    objcopy = str(Path(cc).with_name("arm-none-eabi-objcopy" + suffix))
    subprocess.run([objcopy, "-O", "binary", str(elf), str(elf.with_suffix(".bin"))], check=True)
    print("Firmware generado:", elf)
    if args.bench_channel:
        print("MODO BANCO: solo un canal, 1400-1600 us. START activa 1500 us; no es calibracion mecanica.")


if __name__ == "__main__":
    main()
