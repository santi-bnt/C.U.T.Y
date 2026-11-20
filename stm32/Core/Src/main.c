/* C.U.T.Y STM32F401 firmware entry point.
 *
 * Order matters: pins safe -> RTOS objects -> watchdog -> scheduler.
 * Nothing here can move a servo; see App/rtos/motion_tasks.c for the task
 * topology and docs/freertos-motion-control.md for the bring-up procedure. */
#include "stm32f4xx.h"
#include "cmsis_os2.h"
#include "board_f401.h"
#include "../../App/rtos/motion_tasks.h"

void cuty_fatal(const char *file, int line);
/* Linked with -nostartfiles (no crt0, so no newlib exit/stdio pulled in);
 * the startup file still calls __libc_init_array, which needs these. */
void _init(void);
void _fini(void);
void _init(void) { }
void _fini(void) { }

int main(void) {
    SCB->VTOR = FLASH_BASE;
    NVIC_SetPriorityGrouping(0U); /* every implemented priority bit is pre-emption (FreeRTOS requirement) */
    cuty_board_init();
    if (osKernelInitialize() != osOK || !cuty_rtos_create()) cuty_fatal(__FILE__, __LINE__);
    cuty_board_watchdog_start();
    cuty_rtos_start();            /* does not return */
    cuty_fatal(__FILE__, __LINE__);
    return 0;
}
