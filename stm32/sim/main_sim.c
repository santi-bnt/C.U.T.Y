/* Host simulator entry point: same CMSIS-RTOS2 adapter and FreeRTOS kernel as
 * the Black Pill image, POSIX port underneath. Talk to it over stdin/stdout:
 *     make sim && printf 'V2,HB\n' | build/sim/cuty_sim */
#include "cmsis_os2.h"
#include "../App/rtos/motion_tasks.h"

void cuty_sim_board_start(void);
void cuty_fatal(const char *file, int line);

int main(void) {
    if (osKernelInitialize() != osOK || !cuty_rtos_create()) cuty_fatal(__FILE__, __LINE__);
    cuty_sim_board_start();
    cuty_rtos_start();
    cuty_fatal(__FILE__, __LINE__);
    return 1;
}
