#include "main.h"
#include "cmsis_os2.h"
#include "servo_command.h"
#include "servo_uart.h"
#include <stdbool.h>
#include <string.h>

extern TIM_HandleTypeDef htim4;
extern UART_HandleTypeDef huart2;

/* La interrupcion guarda bytes; la tarea hace todo el trabajo de control. */
typedef struct { uint32_t received_ms; uint8_t byte; } RxByte;
static osMessageQueueId_t rx_queue;
static uint8_t rx_byte;
static volatile bool rx_fault;
/* Orden del repo: 1 = cabeza J7/PB6, 2 = brazo izquierdo J8/PB7,
   3 = brazo derecho J9/PB8. J10/PB9 y J11/PA8 quedan reservados. */
static const uint32_t channels[] = {TIM_CHANNEL_1, TIM_CHANNEL_2, TIM_CHANNEL_3};
static bool running[3];

static void stop_servos(void)
{
    for (unsigned int i = 0; i < 3; ++i) {
        HAL_TIM_PWM_Stop(&htim4, channels[i]);
        running[i] = false;
    }
}

static void reply(const char *message)
{
    /* Respuestas cortas; la Raspberry espera la respuesta antes de enviar mas. */
    if (HAL_UART_Transmit(&huart2, (uint8_t *)message, (uint16_t)strlen(message), 20) != HAL_OK) {
        rx_fault = true;
    }
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *uart)
{
    if (uart->Instance != USART2) return;
    RxByte item = {HAL_GetTick(), rx_byte};
    if (osMessageQueuePut(rx_queue, &item, 0, 0) != osOK) rx_fault = true;
    if (HAL_UART_Receive_IT(&huart2, &rx_byte, 1) != HAL_OK) rx_fault = true;
}

void HAL_UART_ErrorCallback(UART_HandleTypeDef *uart)
{
    if (uart->Instance == USART2) rx_fault = true;
}

void servo_uart_run(void)
{
    char line[32];
    unsigned int length = 0;
    bool discard = false;
    bool stopped_by_fault = false;
    uint32_t last_contact = HAL_GetTick();
    uint32_t last_byte = last_contact;

    /* Arrancamos sin pulsos: ya no existe el barrido automatico de la prueba. */
    stop_servos();
    rx_queue = osMessageQueueNew(64, sizeof(RxByte), NULL);
    if (rx_queue == NULL || HAL_UART_Receive_IT(&huart2, &rx_byte, 1) != HAL_OK) Error_Handler();

    for (;;) {
        uint32_t now = HAL_GetTick();
        if (rx_fault) {
            /* Un error o desbordamiento invalida lo que estaba en recepcion. */
            HAL_NVIC_DisableIRQ(USART2_IRQn);
            HAL_UART_AbortReceive(&huart2);
            osMessageQueueReset(rx_queue);
            rx_fault = false;
            length = 0;
            discard = true;
            stop_servos();
            stopped_by_fault = true;
            if (HAL_UART_Receive_IT(&huart2, &rx_byte, 1) != HAL_OK) Error_Handler();
            HAL_NVIC_EnableIRQ(USART2_IRQn);
        }

        /* Dos segundos sin un comando valido: se apagan los tres PWM. */
        if ((uint32_t)(now - last_contact) >= 2000) {
            stop_servos();
            stopped_by_fault = true;
        }
        if (length > 0 && (uint32_t)(now - last_byte) >= 250) {
            length = 0;
            discard = true;
            stop_servos();
            stopped_by_fault = true;
        }

        RxByte item;
        /* El tick de FreeRTOS es de 1 ms. Al esperar liberamos el procesador. */
        if (osMessageQueueGet(rx_queue, &item, NULL, 10) != osOK) continue;
        if (rx_fault) continue;
        now = HAL_GetTick();
        if ((uint32_t)(now - item.received_ms) >= 250 ||
            (length > 0 && (uint32_t)(item.received_ms - last_byte) >= 250)) {
            discard = true;
            length = 0;
            stop_servos();
            stopped_by_fault = true;
        }
        last_byte = item.received_ms;
        if (item.byte == '\n') {
            if (discard) {
                reply("ERR LINE\n");
            } else if (length > 0) {
                /* Aceptamos tanto LF como CRLF, pero no CR dentro del comando. */
                if (line[length - 1] == '\r') --length;
                line[length] = '\0';
                ServoCommand command = servo_parse_command(line);
                if (command.type == COMMAND_STOP) {
                    stop_servos();
                    stopped_by_fault = false;
                    last_contact = now;
                    reply("OK STOP\n");
                } else if (command.type == COMMAND_INVALID) {
                    stop_servos();
                    stopped_by_fault = true;
                    reply("ERR COMMAND\n");
                } else if (stopped_by_fault) {
                    reply("ERR STOP_REQUIRED\n");
                } else if (command.type == COMMAND_PING) {
                    last_contact = now;
                    reply("OK PING\n");
                } else {
                    unsigned int i = command.servo - 1;
                    __HAL_TIM_SET_COMPARE(&htim4, channels[i], command.pulse_us);
                    if (!running[i] && HAL_TIM_PWM_Start(&htim4, channels[i]) != HAL_OK) {
                        stop_servos();
                        stopped_by_fault = true;
                        reply("ERR PWM\n");
                    } else {
                        running[i] = true;
                        last_contact = now;
                        reply("OK SERVO\n");
                    }
                }
            }
            length = 0;
            discard = false;
        } else if (!discard) {
            if ((item.byte < 32 && item.byte != '\r') || item.byte > 126 || length >= sizeof(line) - 1) {
                /* Nunca ejecutar la cola de un comando roto como otro comando. */
                discard = true;
                stop_servos();
                stopped_by_fault = true;
            } else {
                line[length++] = (char)item.byte;
            }
        }
    }
}
