# C.U.T.Y STM32F401 firmware (FreeRTOS + CMSIS-RTOS2, register-level drivers).
#
#   make                 dry-run image: everything runs, PWM pins never leave GPIO low
#   make PWM=1           image that drives J7..J9 once the Raspberry sends ARM + START
#   make flash-dfu       flash build/f401/cuty.bin over USB (BOOT0 held, tap NRST)
#   make sim             FreeRTOS POSIX simulator of the same tasks (Linux/macOS)
#   make test            host unit tests + simulator scenario test
#   make test-qemu       boots the real ARM image in QEMU and talks to it over USART2
#   make size            flash/RAM usage
#
# Toolchain: arm-none-eabi-gcc (STM32CubeIDE ships one; or apt install
# gcc-arm-none-eabi libnewlib-arm-none-eabi). Host tests need cc + python3.

PWM ?= 0
V ?= 0
Q := $(if $(filter 1,$(V)),,@)
ifeq ($(PWM),1)
  DRY := 0
  VARIANT := f401-pwm
else
  DRY := 1
  VARIANT := f401
endif

CROSS ?= arm-none-eabi-
CC_ARM := $(CROSS)gcc
OBJCOPY := $(CROSS)objcopy
SIZE := $(CROSS)size
HOSTCC ?= cc
PYTHON ?= python3

FREERTOS := Middlewares/Third_Party/FreeRTOS/Source
CMSIS := Drivers/CMSIS
DEVICE := $(CMSIS)/Device/ST/STM32F4xx

APP_SRC := App/communication/uart_protocol.c App/communication/wire.c \
           App/control/body_control.c App/control/fir_filter.c \
           App/power/battery.c App/supervision/liveness.c App/safety/safety.c \
           App/servos/servo.c App/servos/calibration.c App/rtos/motion_tasks.c
KERNEL_SRC := $(FREERTOS)/tasks.c $(FREERTOS)/queue.c $(FREERTOS)/list.c \
              $(FREERTOS)/portable/MemMang/heap_4.c
SHIM_SRC := Core/Src/cmsis_os2_freertos.c

# ------------------------------------------------------------------ target
ARCH := -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard
DEFS := -DSTM32F401xC -DHSE_VALUE=25000000U -DCUTY_RTOS_DRY_RUN=$(DRY) $(EXTRA_DEFS)
INC := -ICore/Inc -I$(FREERTOS)/include -I$(FREERTOS)/portable/GCC/ARM_CM4F \
       -I$(CMSIS)/Include -I$(CMSIS)/RTOS2/Include -I$(DEVICE)/Include
OPT := -O2 -g3 -ffunction-sections -fdata-sections -fno-common
WARN_STRICT := -Wall -Wextra -Werror -Wshadow -Wdouble-promotion
WARN_VENDOR := -w
LDSCRIPT := Core/STM32F401CCUX_FLASH.ld

BUILD := build/$(VARIANT)
TARGET_SRC := $(APP_SRC) $(SHIM_SRC) Core/Src/main.c Core/Src/board_f401.c
VENDOR_SRC := $(KERNEL_SRC) $(FREERTOS)/portable/GCC/ARM_CM4F/port.c $(DEVICE)/Source/system_stm32f4xx.c
STARTUP := $(DEVICE)/Source/startup_stm32f401xc.s

OBJS := $(addprefix $(BUILD)/,$(TARGET_SRC:.c=.o)) $(addprefix $(BUILD)/vendor/,$(VENDOR_SRC:.c=.o)) \
        $(BUILD)/startup.o

.PHONY: all flash-dfu size sim test test-host test-sim test-qemu qemu clean
all: $(BUILD)/cuty.elf $(BUILD)/cuty.bin $(BUILD)/cuty.hex
	@$(SIZE) $(BUILD)/cuty.elf

$(BUILD)/%.o: %.c
	@mkdir -p $(dir $@)
	@echo "  CC   $<"
	$(Q)$(CC_ARM) $(ARCH) $(DEFS) $(INC) $(OPT) -std=c11 $(WARN_STRICT) -MMD -c $< -o $@
$(BUILD)/vendor/%.o: %.c
	@mkdir -p $(dir $@)
	@echo "  CC   $<"
	$(Q)$(CC_ARM) $(ARCH) $(DEFS) $(INC) $(OPT) -std=gnu11 $(WARN_VENDOR) -MMD -c $< -o $@
$(BUILD)/startup.o: $(STARTUP)
	@mkdir -p $(dir $@)
	@echo "  AS   $<"
	$(Q)$(CC_ARM) $(ARCH) -x assembler-with-cpp -c $< -o $@

$(BUILD)/cuty.elf: $(OBJS) $(LDSCRIPT)
	@echo "  LD   $@"
	$(Q)$(CC_ARM) $(ARCH) -T$(LDSCRIPT) -nostartfiles --specs=nano.specs -Wl,--gc-sections \
	  -Wl,-Map=$(BUILD)/cuty.map -Wl,--print-memory-usage $(OBJS) -lm -o $@
$(BUILD)/cuty.bin: $(BUILD)/cuty.elf
	$(Q)$(OBJCOPY) -O binary $< $@
$(BUILD)/cuty.hex: $(BUILD)/cuty.elf
	$(Q)$(OBJCOPY) -O ihex $< $@

size: $(BUILD)/cuty.elf
	$(SIZE) -A $< | grep -E "^\.(isr_vector|text|rodata|data|bss)"

# Black Pill DFU: hold BOOT0, tap NRST, release BOOT0 (same as the Arduino step).
flash-dfu: $(BUILD)/cuty.bin
	dfu-util -a 0 -d 0483:df11 -s 0x08000000:leave -D $<

# QEMU image: same code, SysTick scaled to QEMU's 168 MHz clock, ADC reported absent.
qemu:
	$(MAKE) VARIANT=qemu EXTRA_DEFS=-DCUTY_QEMU=1 all
test-qemu: qemu
	$(PYTHON) tests/qemu_test.py build/qemu/cuty.elf

# ------------------------------------------------------------- simulator
SIM_BUILD := build/sim$(if $(filter 1,$(PWM)),-pwm,)
SIM_SRC := $(APP_SRC) $(SHIM_SRC) sim/board_sim.c sim/main_sim.c
SIM_VENDOR := $(KERNEL_SRC) $(FREERTOS)/portable/ThirdParty/GCC/Posix/port.c \
              $(FREERTOS)/portable/ThirdParty/GCC/Posix/utils/wait_for_event.c
SIM_INC := -Isim -I$(FREERTOS)/include -I$(FREERTOS)/portable/ThirdParty/GCC/Posix \
           -I$(FREERTOS)/portable/ThirdParty/GCC/Posix/utils -I$(CMSIS)/RTOS2/Include

sim: $(SIM_BUILD)/cuty_sim
$(SIM_BUILD)/cuty_sim: $(SIM_SRC) $(SIM_VENDOR) $(wildcard sim/*.h App/*/*.h)
	@mkdir -p $(SIM_BUILD)
	@echo "  SIM  $@"
	$(Q)$(HOSTCC) -std=gnu11 -O1 -g -pthread -DCUTY_SIM=1 -DCUTY_RTOS_DRY_RUN=$(DRY) $(SIM_INC) \
	  -Wall -Wextra -Werror $(SIM_SRC) -w $(SIM_VENDOR) -lm -o $@

# ----------------------------------------------------------------- tests
test-host:
	$(PYTHON) tests/run_host_tests.py
test-sim:
	$(MAKE) PWM=1 sim
	$(PYTHON) tests/sim_test.py build/sim-pwm/cuty_sim
test: test-host test-sim
	@echo "All STM32 tests passed (host unit tests + FreeRTOS simulator)."

clean:
	rm -rf build

-include $(OBJS:.o=.d)
