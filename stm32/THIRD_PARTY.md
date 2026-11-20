# Third-party code in stm32/

Copied unmodified so the firmware builds offline. Only the files the build uses are included.

| Path | Project | Version | License |
| --- | --- | --- | --- |
| `Middlewares/Third_Party/FreeRTOS/Source/` (kernel, `include/`, `portable/GCC/ARM_CM4F`, `portable/MemMang/heap_4.c`, `portable/ThirdParty/GCC/Posix`) | [FreeRTOS-Kernel](https://github.com/FreeRTOS/FreeRTOS-Kernel) | V11.1.0 (`dbf7055`) | MIT, `LICENSE.md` |
| `Drivers/CMSIS/Include/` (`core_cm4.h`, compiler headers, `m-profile/`) and `Drivers/CMSIS/RTOS2/Include/cmsis_os2.h` | [ARM CMSIS 6](https://github.com/ARM-software/CMSIS_6) | v6.1.0 (`b0bbb04`) | Apache-2.0, `Drivers/CMSIS/LICENSE.txt` |
| `Drivers/CMSIS/Device/ST/STM32F4xx/` (`stm32f4xx.h`, `stm32f401xc.h`, `system_stm32f4xx.*`, `startup_stm32f401xc.s`) | [STMicroelectronics cmsis_device_f4](https://github.com/STMicroelectronics/cmsis_device_f4) | v2.6.10 (`5f41fb2`) | Apache-2.0, `LICENSE.md` |

`Core/Src/cmsis_os2_freertos.c` is our own small CMSIS-RTOS2 layer (only the calls the
firmware uses); it is not ARM's CMSIS-FreeRTOS wrapper.
