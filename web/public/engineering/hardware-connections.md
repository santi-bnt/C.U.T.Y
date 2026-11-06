# C.U.T.Y. — confirmed hardware connections

Source: builder-supplied connection table, 2026-11-06. Display and ReSpeaker operation together is confirmed by the user. This document records that evidence; CAD connector mappings are a separate design reference.

## Raspberry Pi 5 → Waveshare 3.5-inch (G)

| Function    | BCM | Physical pin |
| ----------- | --- | ------------ |
| 3.3 V       | —   | 1            |
| 5 V         | —   | 4            |
| GND         | —   | 6            |
| Touch IRQ   | 17  | 11           |
| LCD DC / RS | 24  | 18           |
| SPI MOSI    | 10  | 19           |
| SPI MISO    | 9   | 21           |
| LCD RESET   | 25  | 22           |
| SPI SCLK    | 11  | 23           |
| LCD CS      | 8   | 24           |
| Touch CS    | 7   | 26           |

DC and RESET use the modified working assignments. Backlight and final overlay require comparison with the physical setup. Keep the working GPIO/overlay configuration.

## Raspberry Pi 5 → ReSpeaker 2-Mics Pi HAT V2.0

| Function  | BCM | Physical pin |
| --------- | --- | ------------ |
| 5 V       | —   | 2            |
| 3.3 V     | —   | 17           |
| GND       | —   | 39           |
| I2C SDA   | 2   | 3            |
| I2C SCL   | 3   | 5            |
| MCLK      | 4   | 7            |
| I2S BCLK  | 18  | 12           |
| I2S LRCLK | 19  | 35           |
| I2S DIN   | 20  | 38           |
| I2S DOUT  | 21  | 40           |
| AUD_RST   | 26  | 37           |

This is the user's latest explicit ReSpeaker table, superseding the earlier alternative power/ground pins. MCLK is physical 7 / BCM4 and AUD_RST is physical 37 / BCM26. BCM10/11 belong to display SPI: do not use ReSpeaker RGB LEDs. BCM17 belongs to display Touch IRQ: do not use the ReSpeaker button. BCM18 is I2S BCLK: do not use it for backlight. Preserve the working GPIO and overlay configuration.

## Camera

Arducam OV5647 CSI 15-pin → Pi 5 CAM/DISP 22-pin using a compatible 15-to-22-pin cable. CSI supplies power and image signals. No individual ribbon-contact mapping is asserted.

## Proposed UART and servo control

Pi physical 8 / BCM14 TXD → STM32 RX pin to confirm. STM32 TX pin to confirm → Pi physical 10 / BCM15 RXD. Shared GND, 3.3 V logic; do not apply 5 V UART signals.

Five MG996R: red → regulated 6 V; brown/black → servo GND; orange/yellow → STM32 PWM. All five final PWM pin assignments are pending.

## Power

LiPo 3S: 11.1 V nominal, 12.6 V full, 2200 mAh, 24.42 Wh, label 50C. Battery +/− → buck IN+/IN−; OUT+ → servo positive; OUT− → servo ground. Adjust and measure approximately 6.0 V before servo connection. Exact converter model and simultaneous current capacity are pending.

Share electrical GND between Pi, STM32 and servo supply. Do not join positive outputs of different-voltage regulators. Pi requires a compatible 5.1 V USB-C supply with sufficient current. Never connect raw LiPo directly to the Pi. A separate battery-to-Pi regulator still needs definition and validation.

## Remaining checks

Display backlight/overlay; STM32 UART pins; five PWM pins; battery protection/fuse/distribution; buck model/current; battery-to-Pi supply; final PCB distribution/connectors. Proposed assignments are not physically proven by the confirmed display/audio test.
