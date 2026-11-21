/* Simula UART y reloj para probar la tarea real sin conectar servomotores. */
#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../Core/Src/servo_uart.c"

TIM_HandleTypeDef htim4;
UART_HandleTypeDef huart2 = {USART2};
static jmp_buf finished;
static uint32_t clock_ms, finish_ms;
static struct { uint32_t time; unsigned char byte; } events[1024];
static unsigned int event_count, next_event, starts[3], pulses[3];
static char responses[4096];
static RxByte queued;
static bool has_byte, fail_pwm, fail_queue;
static bool enabled[3];

uint32_t HAL_GetTick(void) { return clock_ms; }
void fake_compare(uint32_t channel, uint32_t pulse) { pulses[channel] = pulse; }
HAL_StatusTypeDef HAL_TIM_PWM_Start(TIM_HandleTypeDef *t, uint32_t c)
{ (void)t; if (fail_pwm) return HAL_ERROR; ++starts[c]; enabled[c] = true; return HAL_OK; }
HAL_StatusTypeDef HAL_TIM_PWM_Stop(TIM_HandleTypeDef *t, uint32_t c)
{ (void)t; enabled[c] = false; return HAL_OK; }
HAL_StatusTypeDef HAL_UART_Receive_IT(UART_HandleTypeDef *u, uint8_t *b, uint16_t n)
{ (void)u; (void)b; (void)n; return HAL_OK; }
HAL_StatusTypeDef HAL_UART_AbortReceive(UART_HandleTypeDef *u)
{ (void)u; return HAL_OK; }
HAL_StatusTypeDef HAL_UART_Transmit(UART_HandleTypeDef *u, uint8_t *b, uint16_t n, uint32_t t)
{
    (void)u; (void)t;
    assert(strlen(responses) + n < sizeof responses);
    strncat(responses, (char *)b, n);
    return HAL_OK;
}
void HAL_NVIC_DisableIRQ(int irq) { (void)irq; }
void HAL_NVIC_EnableIRQ(int irq) { (void)irq; }
void Error_Handler(void) { abort(); }
osMessageQueueId_t osMessageQueueNew(uint32_t n, uint32_t s, const void *a)
{ (void)n; (void)s; (void)a; return &queued; }
osStatus_t osMessageQueuePut(osMessageQueueId_t q, const void *p, uint8_t pri, uint32_t t)
{
    (void)q; (void)pri; (void)t;
    if (fail_queue) { fail_queue = false; return osErrorTimeout; }
    queued = *(const RxByte *)p; has_byte = true; return osOK;
}
osStatus_t osMessageQueueReset(osMessageQueueId_t q)
{ (void)q; has_byte = false; return osOK; }
osStatus_t osMessageQueueGet(osMessageQueueId_t q, void *p, uint8_t *pri, uint32_t t)
{
    (void)q; (void)pri;
    if (clock_ms >= finish_ms) longjmp(finished, 1);
    if (next_event < event_count && events[next_event].time <= clock_ms) {
        rx_byte = events[next_event++].byte;
        HAL_UART_RxCpltCallback(&huart2);
        if (has_byte) { *(RxByte *)p = queued; has_byte = false; return osOK; }
    }
    clock_ms += t;
    return osErrorTimeout;
}

static void reset(void)
{
    clock_ms = event_count = next_event = 0;
    finish_ms = 1000;
    responses[0] = '\0';
    rx_fault = has_byte = fail_pwm = fail_queue = false;
    memset(starts, 0, sizeof starts);
    memset(pulses, 0, sizeof pulses);
    memset(enabled, 0, sizeof enabled);
}
static void at(uint32_t time, const char *text)
{
    while (*text) {
        assert(event_count < 1024);
        events[event_count].time = time;
        events[event_count++].byte = (unsigned char)*text++;
    }
}
static void run(void) { if (setjmp(finished) == 0) servo_uart_run(); }

int main(void)
{
    const char *bad[] = {"", "SERVO,0,1500", "SERVO,4,1500", "SERVO,1,0999",
        "SERVO,1,2001", "SERVO,1,15000", "SERVO,1,1500x", "SERVO,1,+500",
        "SERVO,1,", "SERVO,1", "SERVO,", "SERVO,1,1", "PING ", "STOP,1"};
    for (unsigned int i = 0; i < sizeof bad / sizeof bad[0]; ++i)
        assert(servo_parse_command(bad[i]).type == COMMAND_INVALID);

    reset(); run(); assert(starts[0] + starts[1] + starts[2] == 0);
    reset(); at(0, "STOP\nPING\nSERVO,1,1000\nSERVO,2,1500\r\nSERVO,3,2000\n"); run();
    assert(starts[0] == 1 && starts[1] == 1 && starts[2] == 1);
    assert(pulses[0] == 1000 && pulses[1] == 1500 && pulses[2] == 2000);
    assert(strstr(responses, "ERR") == NULL);
    assert(enabled[0] && enabled[1] && enabled[2]);

    reset(); finish_ms = 2200; at(0, "SERVO,1,1500\n"); run();
    assert(starts[0] == 1 && !enabled[0]);
    reset(); finish_ms = 3100; at(0, "SERVO,1,1500\n");
    at(500, "PING\n"); at(1000, "PING\n"); at(1500, "PING\n");
    at(2000, "PING\n"); at(2500, "PING\n"); run();
    assert(enabled[0] && strstr(responses, "ERR") == NULL);

    reset(); finish_ms = 3200; at(0, "SERVO,1,1500\n");
    at(2200, "PING\nSERVO,2,1500\nSTOP\nSERVO,3,1500\n"); run();
    assert(starts[1] == 0 && starts[2] == 1 && !running[0]);
    assert(strstr(responses, "ERR STOP_REQUIRED\n") != NULL);

    reset(); at(0, "SERVO,1,1500\nINVALID\nSERVO,2,1500\n"); run();
    assert(!running[0] && !enabled[0] && starts[1] == 0);
    assert(strstr(responses, "ERR COMMAND\n") != NULL);

    reset(); at(0, "SERVO,1,"); at(300, "1500\nSERVO,2,1500\n"); run();
    assert(starts[0] + starts[1] == 0);
    reset(); at(0, "012345678901234567890123456789012345SERVO,1,1500\n"); run();
    assert(starts[0] == 0 && strstr(responses, "ERR LINE\n") != NULL);
    reset(); at(0, "SERVO,1,"); at(0, "\0011500\nSERVO,2,1500\n"); run();
    assert(starts[0] + starts[1] == 0);

    reset(); fail_pwm = true; at(0, "SERVO,1,1500\n"); run();
    assert(!running[0] && strstr(responses, "ERR PWM\n") != NULL);
    reset(); fail_queue = true; at(0, "SERVO,1,1500\nSERVO,2,1500\nSTOP\nSERVO,3,1500\n"); run();
    assert(starts[0] + starts[1] == 0 && starts[2] == 1);
    puts("PASS: parser, PWM, timeout, STOP recovery, malformed/partial input, RX overflow");
}
