# Wiring

Interactive reference: [block connection diagram (standalone HTML)](conexiones.html), with signal/power views and pin tables generated from the carrier netlist. Static images: [signals](assets/conexiones-senales.svg) and [power](assets/conexiones-alimentacion.svg). It documents the carrier design, not a verified physical wiring inspection.

The carrier PCB v1.1 is designed for Raspberry Pi 5 and STM32F401 Black Pill: [hardware/electronics/kicad/cuty_carrier](../hardware/electronics/kicad/cuty_carrier/README.md) (KiCad 7 project, Gerbers, BOM, schematic PDF). In this design, the display and Raspberry Pi connect by keyed ribbon cables; the ReSpeaker plugs in directly. These are carrier connections, not confirmation of the current manually wired assembly.

Links on the board: Raspberry Pi 5 ↔ STM32 UART (Pi TX pin 8 → PA3, PA2 → Pi RX pin 10); STM32 PB6–PB9 and PA8 → five MG996R at 6 V; battery divider on PA1; Pi header → Display-G 26-pin and ReSpeaker 2-Mics HAT (same physical pin numbering); LiPo 3S → fuses → servo buck (6 V) and Pi regulator (5.1 V USB-C). Power ground (PGND) and logic ground (GND) meet only at net tie NT1.

Already tested in the manually wired Pi setup: ReSpeaker capture and speaker playback, plus the SPI touchscreen. These tests do not validate the unassembled carrier. Still to validate on the carrier: fabrication/assembly, Pi-to-STM32F401 UART, audio/display routing and power distribution, including the proposed 5.1 V / 5 A regulator. Firmware is not implemented yet. The board design includes fuses only; LiPo over-discharge protection and a balance charger remain separate requirements.
