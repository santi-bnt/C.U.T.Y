"""Compila el firmware con GCC para ARM. No descarga herramientas ni graba la placa."""
import argparse
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cc", help="Ruta a arm-none-eabi-gcc, si no esta en PATH")
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
    output.mkdir(exist_ok=True)
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


if __name__ == "__main__":
    main()
