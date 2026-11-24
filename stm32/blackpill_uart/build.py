"""Compila el firmware con GCC para ARM. No descarga herramientas ni graba la placa."""
import argparse
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cc", help="Ruta a arm-none-eabi-gcc, si no esta en PATH")
    parser.add_argument("--bench-channel", type=int, choices=(1, 2, 3),
                        help="PWM de banco en un solo canal: 1=J7/PB6, 2=J8/PB7, 3=J9/PB8; solo servo suelto")
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
    elf = output / "cuty_arms_pwm_blackpill.elf"
    # Una sola orden mantiene este ejemplo facil de leer y de reproducir.
    command = [cc, "-mcpu=cortex-m4", "-mthumb", "-mfpu=fpv4-sp-d16",
               "-mfloat-abi=hard", "-std=gnu11", "-Og", "-g3", "-Wall", "-Wextra",
               "-ffunction-sections", "-fdata-sections", "-DUSE_HAL_DRIVER",
               "-DSTM32F401xC", "--specs=nano.specs", "--specs=nosys.specs"]
    command += ["-I" + str(root / include) for include in includes]
    if args.bench_channel:
        command += [f"-DCUTY_BENCH_CHANNEL={args.bench_channel}"]
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
