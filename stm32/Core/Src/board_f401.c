/* Register-level board support for the STM32F401CC Black Pill on the C.U.T.Y
 * carrier v1.1. Implements App/board/cuty_board.h. See board_f401.h for the
 * pin/peripheral map. Everything that can move a servo starts disabled. */
#include "board_f401.h"
#include "stm32f4xx.h"
#include "FreeRTOS.h"
#include "task.h"
#include "../../App/board/cuty_board.h"
#include "../../App/power/battery.h"
#include "../../App/rtos/motion_tasks.h"

#if !defined(CUTY_RTOS_DRY_RUN)
#error "CUTY_RTOS_DRY_RUN must be defined by the build (1 = dry run, 0 = PWM)."
#endif
#define PWM_BUILD (CUTY_RTOS_DRY_RUN == 0)

#define PWM_PINS_B ((1U << 6) | (1U << 7) | (1U << 8)) /* J7, J8, J9 */
#define RESERVED_PIN_B9 (1U << 9)                     /* J10 */
#define RESERVED_PIN_A8 (1U << 8)                     /* J11 */
#define PWM_CCER (TIM_CCER_CC1E | TIM_CCER_CC2E | TIM_CCER_CC3E)
#define TX_RING 1024U

static CutyWireBoot boot_info;
static uint32_t pclk1_hz, tim4_hz;
static volatile bool outputs_on, outputs_killed, watchdog_running;
static char tx_ring[TX_RING];
static volatile uint32_t tx_head, tx_tail; /* head: TxTask, tail: USART2 IRQ */

static inline uint32_t lock(void) { uint32_t primask = __get_PRIMASK(); __disable_irq(); return primask; }
static inline void unlock(uint32_t primask) { __set_PRIMASK(primask); }

static bool wait_set(volatile uint32_t *reg, uint32_t mask, uint32_t value, uint32_t loops) {
    while (loops--) if ((*reg & mask) == value) return true;
    return false;
}

static void gpio_mode(GPIO_TypeDef *port, uint32_t pin, uint32_t mode, uint32_t af) {
    uint32_t shift = pin * 2U;
    if (mode == 2U) {
        volatile uint32_t *afr = &port->AFR[pin >> 3U];
        uint32_t s = (pin & 7U) * 4U;
        *afr = (*afr & ~(0xFU << s)) | (af << s);
    }
    port->MODER = (port->MODER & ~(3U << shift)) | (mode << shift);
}

static void pins_low_output(GPIO_TypeDef *port, uint32_t mask) {
    port->BSRR = mask << 16U; /* drive low first, then switch to output */
    for (uint32_t pin = 0; pin < 16U; ++pin) if (mask & (1U << pin)) gpio_mode(port, pin, 1U, 0U);
}

/* ---------------------------------------------------------------- clocks */
static void clock_init(void) {
    RCC->APB1ENR |= RCC_APB1ENR_PWREN; (void)RCC->APB1ENR;
    PWR->CR = (PWR->CR & ~PWR_CR_VOS) | PWR_CR_VOS_1; /* scale 2: up to 84 MHz */
    FLASH->ACR = FLASH_ACR_LATENCY_2WS | FLASH_ACR_PRFTEN | FLASH_ACR_ICEN | FLASH_ACR_DCEN;

    RCC->CR |= RCC_CR_HSEON;
    bool hse = wait_set(&RCC->CR, RCC_CR_HSERDY, RCC_CR_HSERDY, 200000U);
    if (!hse) RCC->CR &= ~RCC_CR_HSEON;
    /* VCO input 1 MHz (HSE 25/25 or HSI 16/16), VCO 336 MHz, SYSCLK /4 = 84 MHz, USB /7 = 48 MHz. */
    RCC->PLLCFGR = ((hse ? 25U : 16U) << RCC_PLLCFGR_PLLM_Pos) | (336U << RCC_PLLCFGR_PLLN_Pos) |
                   (1U << RCC_PLLCFGR_PLLP_Pos) | (7U << RCC_PLLCFGR_PLLQ_Pos) |
                   (hse ? RCC_PLLCFGR_PLLSRC_HSE : 0U);
    RCC->CR |= RCC_CR_PLLON;
    bool pll = wait_set(&RCC->CR, RCC_CR_PLLRDY, RCC_CR_PLLRDY, 200000U);
    if (pll) {
        RCC->CFGR = (RCC->CFGR & ~(RCC_CFGR_HPRE | RCC_CFGR_PPRE1 | RCC_CFGR_PPRE2 | RCC_CFGR_SW)) |
                    RCC_CFGR_HPRE_DIV1 | RCC_CFGR_PPRE1_DIV2 | RCC_CFGR_PPRE2_DIV1 | RCC_CFGR_SW_PLL;
        pll = wait_set(&RCC->CFGR, RCC_CFGR_SWS, RCC_CFGR_SWS_PLL, 200000U);
    }
    if (pll) { SystemCoreClock = 84000000U; pclk1_hz = 42000000U; tim4_hz = 84000000U; }
    else {
        /* Stay on HSI 16 MHz, all buses /1. Slower but fully functional. */
        RCC->CFGR &= ~(RCC_CFGR_HPRE | RCC_CFGR_PPRE1 | RCC_CFGR_PPRE2 | RCC_CFGR_SW);
        RCC->CR &= ~RCC_CR_PLLON;
        SystemCoreClock = 16000000U; pclk1_hz = 16000000U; tim4_hz = 16000000U;
    }
    boot_info.hse = hse && pll;
#if defined(CUTY_QEMU)
    /* QEMU netduinoplus2 clocks SysTick from its fixed 168 MHz SYSCLK. */
    SystemCoreClock = 168000000U;
#endif
    boot_info.sysclk_hz = SystemCoreClock;
}

static void reset_cause(void) {
    uint32_t csr = RCC->CSR;
    boot_info.reset = (csr & RCC_CSR_IWDGRSTF) ? CUTY_RESET_WATCHDOG :
                      (csr & RCC_CSR_SFTRSTF)  ? CUTY_RESET_SOFTWARE :
                      (csr & RCC_CSR_PORRSTF)  ? CUTY_RESET_POWER :
                      (csr & RCC_CSR_BORRSTF)  ? CUTY_RESET_BROWNOUT :
                      (csr & RCC_CSR_PINRSTF)  ? CUTY_RESET_PIN : CUTY_RESET_OTHER;
    RCC->CSR |= RCC_CSR_RMVF;
}

/* ------------------------------------------------------------------- PWM */
static void pwm_init(void) {
    RCC->APB1ENR |= RCC_APB1ENR_TIM4EN; (void)RCC->APB1ENR;
    TIM4->CR1 = 0;
    TIM4->PSC = tim4_hz / 1000000U - 1U; /* 1 us per count */
    TIM4->ARR = 19999U;                   /* 20 ms period */
    TIM4->CCMR1 = (6U << TIM_CCMR1_OC1M_Pos) | TIM_CCMR1_OC1PE | (6U << TIM_CCMR1_OC2M_Pos) | TIM_CCMR1_OC2PE;
    TIM4->CCMR2 = (6U << TIM_CCMR2_OC3M_Pos) | TIM_CCMR2_OC3PE;
    TIM4->CCR1 = TIM4->CCR2 = TIM4->CCR3 = 1500U;
    TIM4->CCER = 0; /* channels disabled; pins are plain GPIO low anyway */
    TIM4->CR1 = TIM_CR1_ARPE;
    TIM4->EGR = TIM_EGR_UG;
    TIM4->CR1 |= TIM_CR1_CEN;
}

/* Switch pins only between pulses (counter past the longest 2.5 ms pulse) so
 * enabling or releasing never emits a runt pulse. The servo task calls every
 * 10 ms, i.e. twice per 20 ms period, so one of two calls hits the window. */
static bool between_pulses(void) { uint32_t c = TIM4->CNT; return c > 2600U && c < 19500U; }

void cuty_board_set_outputs(const uint16_t pulse_us[CUTY_AXES], bool enable) {
    uint32_t key = lock();
    TIM4->CCR1 = pulse_us[0]; TIM4->CCR2 = pulse_us[1]; TIM4->CCR3 = pulse_us[2]; /* preloaded */
    bool want = enable && PWM_BUILD && !outputs_killed;
    if (want != outputs_on && between_pulses()) {
        if (want) {
            TIM4->CCER |= PWM_CCER;
            for (uint32_t pin = 6U; pin <= 8U; ++pin) gpio_mode(GPIOB, pin, 2U, 2U); /* AF2 = TIM4 */
        } else {
            pins_low_output(GPIOB, PWM_PINS_B);
            TIM4->CCER &= ~PWM_CCER;
        }
        outputs_on = want;
    }
    unlock(key);
}

static void kill_now(void) {
    outputs_killed = true;
    pins_low_output(GPIOB, PWM_PINS_B | RESERVED_PIN_B9);
    pins_low_output(GPIOA, RESERVED_PIN_A8);
    TIM4->CCER = 0;
    outputs_on = false;
}

void cuty_board_kill_outputs(void) { uint32_t key = lock(); kill_now(); unlock(key); }
bool cuty_board_outputs_enabled(void) { return outputs_on; }

/* ------------------------------------------------------------------ UART */
static void uart_init(void) {
    RCC->APB1ENR |= RCC_APB1ENR_USART2EN; (void)RCC->APB1ENR;
    GPIOA->PUPDR = (GPIOA->PUPDR & ~(3U << (3U * 2U))) | (1U << (3U * 2U)); /* RX idles high */
    gpio_mode(GPIOA, 2U, 2U, 7U);
    gpio_mode(GPIOA, 3U, 2U, 7U);
    USART2->BRR = (pclk1_hz + CUTY_UART_BAUD / 2U) / CUTY_UART_BAUD; /* OVER8 = 0 */
    USART2->CR1 = USART_CR1_TE | USART_CR1_RE | USART_CR1_RXNEIE;
    USART2->CR1 |= USART_CR1_UE;
    NVIC_SetPriority(USART2_IRQn, 6U); /* below configMAX_SYSCALL (5): FromISR calls allowed */
    NVIC_EnableIRQ(USART2_IRQn);
}

void USART2_IRQHandler(void) {
    uint32_t sr = USART2->SR;
    if (sr & (USART_SR_RXNE | USART_SR_ORE | USART_SR_FE | USART_SR_NE)) {
        uint8_t byte = (uint8_t)USART2->DR; /* SR then DR read clears the error flags */
        if (sr & (USART_SR_ORE | USART_SR_FE | USART_SR_NE)) cuty_uart_rx_error_isr();
        else cuty_uart_rx_isr(byte);
    }
    if ((USART2->CR1 & USART_CR1_TXEIE) && (sr & USART_SR_TXE)) {
        uint32_t tail = tx_tail;
        if (tail != tx_head) { USART2->DR = (uint8_t)tx_ring[tail]; tx_tail = (tail + 1U) % TX_RING; }
        else USART2->CR1 &= ~USART_CR1_TXEIE;
    }
}

size_t cuty_board_uart_tx_free(void) { return TX_RING - 1U - (tx_head - tx_tail + TX_RING) % TX_RING; }

size_t cuty_board_uart_write(const char *data, size_t length) {
    size_t n = 0;
    while (n < length && cuty_board_uart_tx_free() > 0U) {
        tx_ring[tx_head] = data[n++];
        tx_head = (tx_head + 1U) % TX_RING;
    }
    uint32_t key = lock(); USART2->CR1 |= USART_CR1_TXEIE; unlock(key);
    return n;
}

/* ------------------------------------------------------------------- ADC */
static void adc_init(void) {
    RCC->APB2ENR |= RCC_APB2ENR_ADC1EN; (void)RCC->APB2ENR;
    gpio_mode(GPIOA, 1U, 3U, 0U);                     /* PA1 analog */
    ADC->CCR = (ADC->CCR & ~ADC_CCR_ADCPRE) | ADC_CCR_ADCPRE_0; /* PCLK2/4 = 21 MHz */
    ADC1->SMPR2 = 7U << ADC_SMPR2_SMP1_Pos;           /* 480 cycles: 18 kOhm divider */
    ADC1->SQR1 = 0;                                   /* one conversion */
    ADC1->SQR3 = 1U;                                  /* channel 1 */
    ADC1->CR2 = ADC_CR2_ADON;
}

uint32_t cuty_board_battery_mv(void) {
#if defined(CUTY_QEMU)
    return 0U; /* no meaningful ADC in QEMU: report "no pack" */
#else
    ADC1->CR2 |= ADC_CR2_SWSTART;
    if (!wait_set(&ADC1->SR, ADC_SR_EOC, ADC_SR_EOC, 20000U)) return 0U;
    return cuty_battery_mv_from_raw((uint16_t)(ADC1->DR & 0xFFFU));
#endif
}

/* ---------------------------------------------------------- watchdog/LED */
void cuty_board_watchdog_start(void) {
    DBGMCU->APB1FZ |= DBGMCU_APB1_FZ_DBG_IWDG_STOP; /* halting in a debugger does not reset */
    IWDG->KR = 0x5555U;
    IWDG->PR = 1U;     /* LSI / 8 */
    IWDG->RLR = 999U;  /* ~250 ms nominal */
    IWDG->KR = 0xAAAAU;
    IWDG->KR = 0xCCCCU;
    watchdog_running = true;
}
void cuty_board_watchdog_kick(void) { IWDG->KR = 0xAAAAU; }

void cuty_board_led(bool on) { GPIOC->BSRR = on ? (1U << (13U + 16U)) : (1U << 13U); } /* active low */

void cuty_board_info(CutyWireBoot *info) { *info = boot_info; }
uint32_t cuty_board_heap_min_free(void) { return (uint32_t)xPortGetMinimumEverFreeHeapSize(); }

/* ------------------------------------------------------------------ init */
void cuty_board_init(void) {
    reset_cause();
    clock_init();
    boot_info.pwm_build = PWM_BUILD;
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN | RCC_AHB1ENR_GPIOBEN | RCC_AHB1ENR_GPIOCEN; (void)RCC->AHB1ENR;
    /* Servo signal pins (J7..J11) low before anything else: no pulses, servos limp. */
    pins_low_output(GPIOB, PWM_PINS_B | RESERVED_PIN_B9);
    pins_low_output(GPIOA, RESERVED_PIN_A8);
    GPIOC->BSRR = 1U << 13U; gpio_mode(GPIOC, 13U, 1U, 0U); /* LED off */
    pwm_init();
    adc_init();
    uart_init();
}

/* ------------------------------------------------------------ fatal path */
void cuty_fatal(const char *file, int line) {
    (void)file; (void)line;
    __disable_irq();
    kill_now();
    GPIOC->BSRR = 1U << (13U + 16U); /* LED on */
    if (!watchdog_running) cuty_board_watchdog_start();
    for (;;) { } /* IWDG resets the MCU; outputs come back disabled */
}

void vApplicationStackOverflowHook(TaskHandle_t task, char *name) { (void)task; (void)name; cuty_fatal(__FILE__, __LINE__); }
void vApplicationMallocFailedHook(void) { cuty_fatal(__FILE__, __LINE__); }
void NMI_Handler(void) { cuty_fatal(__FILE__, __LINE__); }
void HardFault_Handler(void) { cuty_fatal(__FILE__, __LINE__); }
void MemManage_Handler(void) { cuty_fatal(__FILE__, __LINE__); }
void BusFault_Handler(void) { cuty_fatal(__FILE__, __LINE__); }
void UsageFault_Handler(void) { cuty_fatal(__FILE__, __LINE__); }
