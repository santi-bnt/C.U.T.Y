# STM32 Core

Black Pill (STM32F401CCU6) board support, register-level with CMSIS headers, no HAL.

- `Src/main.c`: pins safe, then RTOS objects, then IWDG, then scheduler.
- `Src/board_f401.c`: 25 MHz HSE → 84 MHz PLL (HSI fallback); USART2 PA2/PA3 IRQ RX + TX ring;
  TIM4 CH1–3 PWM on PB6–PB8 with an output gate that only switches between pulses; ADC1 PA1
  battery; IWDG; PC13 LED; fatal handlers that force the servo pins low.
- `Src/cmsis_os2_freertos.c`: the CMSIS-RTOS2 calls the firmware uses, on FreeRTOS (shared with the simulator).
- `Inc/FreeRTOSConfig.h`: 1 kHz tick, 56 priorities (CMSIS mapping), heap_4 24 KiB,
  max syscall interrupt priority 5 (USART2 runs at 6).
- `STM32F401CCUX_FLASH.ld`: 256 KiB flash, 64 KiB RAM.

See [docs/freertos-motion-control.md](../../docs/freertos-motion-control.md) for the bring-up procedure.
