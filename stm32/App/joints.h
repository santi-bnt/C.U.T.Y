#ifndef CUTY_JOINTS_H
#define CUTY_JOINTS_H
/* Logical joints only; carrier routing is design evidence, not bench validation. */
#define CUTY_AXES 3U
#define CUTY_PCB_CHANNELS 5U
typedef enum {
    CUTY_HEAD_PAN = 0,
    CUTY_LEFT_ARM = 1,
    CUTY_RIGHT_ARM = 2
} CutyJoint;
/* J7/PB6/TIM4_CH1, J8/PB7/TIM4_CH2, J9/PB8/TIM4_CH3 are proposed.
 * J10/PB9/TIM4_CH4 and J11/PA8/TIM1_CH1 stay reserved, disabled and unassigned.
 * No peripheral initialization or output enable is provided by this header. */
#endif
