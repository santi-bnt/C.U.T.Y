/* Simulated C.U.T.Y carrier for the FreeRTOS POSIX port.
 *
 *   USART2  stdin (bytes in) / stdout (records out). A top-priority FreeRTOS
 *           task stands in for the RX interrupt and calls cuty_uart_rx_isr().
 *   PWM     "SIM,PWM,<enabled>,<j7>,<j8>,<j9>" on stderr whenever it changes.
 *   Battery millivolts read from $CUTY_SIM_BATTERY_FILE (default 11800 mV).
 *   IWDG    a plain pthread (signals blocked) exits with code 3 after 250 ms
 *           without a refresh, printing "SIM,WATCHDOG_RESET".
 *   Fault injection: while $CUTY_SIM_STALL_FILE exists, the next output call
 *           from ServoControlTask never returns (a stuck control task). */
#include "../App/board/cuty_board.h"
#include "../App/rtos/motion_tasks.h"
#include "FreeRTOS.h"
#include "task.h"
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define WATCHDOG_MS 250U

static volatile int outputs_on = 0, killed = 0;
static uint16_t shown[CUTY_AXES];
static int shown_enable = -1;
static volatile uint64_t last_kick_ms;
static volatile int watchdog_armed;

static uint64_t mono_ms(void) {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000U + (uint64_t)ts.tv_nsec / 1000000U;
}

static void say(const char *text) {
    size_t n = strlen(text);
    while (n) { ssize_t w = write(2, text, n); if (w < 0) { if (errno == EINTR) continue; return; } text += w; n -= (size_t)w; }
}

void cuty_board_info(CutyWireBoot *info) {
    info->reset = CUTY_RESET_POWER; info->hse = false;
    info->pwm_build = CUTY_RTOS_DRY_RUN == 0; info->sysclk_hz = 0;
}

void cuty_board_set_outputs(const uint16_t pulse_us[CUTY_AXES], bool enable) {
    const char *stall = getenv("CUTY_SIM_STALL_FILE");
    if (stall && access(stall, F_OK) == 0) {
        say("SIM,STALL\n");
        for (;;) vTaskDelay(1000); /* ServoControlTask is now stuck */
    }
    int on = enable && !killed && CUTY_RTOS_DRY_RUN == 0;
    outputs_on = on;
    if (on != shown_enable || memcmp(shown, pulse_us, sizeof shown)) {
        char line[64];
        snprintf(line, sizeof line, "SIM,PWM,%d,%u,%u,%u\n", on, pulse_us[0], pulse_us[1], pulse_us[2]);
        say(line); shown_enable = on; memcpy(shown, pulse_us, sizeof shown);
    }
}

void cuty_board_kill_outputs(void) {
    if (!killed) say("SIM,KILL\n");
    killed = 1; outputs_on = 0;
}
bool cuty_board_outputs_enabled(void) { return outputs_on; }

uint32_t cuty_board_battery_mv(void) {
    const char *path = getenv("CUTY_SIM_BATTERY_FILE");
    FILE *f = path ? fopen(path, "r") : NULL;
    if (!f) return 11800U;
    unsigned mv = 11800U;
    if (fscanf(f, "%u", &mv) != 1) mv = 11800U;
    fclose(f);
    return mv;
}

void cuty_board_watchdog_kick(void) { last_kick_ms = mono_ms(); watchdog_armed = 1; }

size_t cuty_board_uart_tx_free(void) { return 4096U; }
size_t cuty_board_uart_write(const char *data, size_t length) {
    size_t left = length;
    while (left) {
        ssize_t w = write(1, data, left);
        if (w < 0) { if (errno == EINTR || errno == EAGAIN) continue; break; }
        data += w; left -= (size_t)w;
    }
    return length - left;
}

void cuty_board_led(bool on) { (void)on; }
uint32_t cuty_board_heap_min_free(void) { return (uint32_t)xPortGetMinimumEverFreeHeapSize(); }

/* --- simulated USART2 RX interrupt: highest-priority task polling stdin --- */
static void uart_rx_task(void *unused) {
    (void)unused;
    for (;;) {
        unsigned char buf[64];
        ssize_t n = read(0, buf, sizeof buf);
        if (n > 0) { for (ssize_t i = 0; i < n; ++i) cuty_uart_rx_isr(buf[i]); continue; }
        if (n == 0) { say("SIM,EOF\n"); _exit(0); } /* host closed the "UART" */
        vTaskDelay(1);
    }
}

static void *watchdog_thread(void *unused) {
    (void)unused;
    for (;;) {
        usleep(5000);
        if (watchdog_armed && mono_ms() - last_kick_ms > WATCHDOG_MS) {
            say("SIM,WATCHDOG_RESET\n"); _exit(3);
        }
    }
    return NULL;
}

void cuty_sim_board_start(void) {
    fcntl(0, F_SETFL, fcntl(0, F_GETFL) | O_NONBLOCK);
    /* Non-FreeRTOS threads must not receive the port's tick signal. */
    sigset_t all, old; sigfillset(&all);
    pthread_sigmask(SIG_SETMASK, &all, &old);
    pthread_t thread; pthread_create(&thread, NULL, watchdog_thread, NULL); pthread_detach(thread);
    pthread_sigmask(SIG_SETMASK, &old, NULL);
    xTaskCreate(uart_rx_task, "Usart2RxIrq", 1024, NULL, configMAX_PRIORITIES - 1, NULL);
}

void cuty_fatal(const char *file, int line) {
    char text[160]; snprintf(text, sizeof text, "SIM,FATAL,%s:%d\n", file, line); say(text);
    _exit(4);
}
void vApplicationMallocFailedHook(void) { cuty_fatal(__FILE__, __LINE__); }
