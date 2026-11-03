# Wiring

The carrier PCB is designed: [hardware/electronics/kicad/cuty_carrier](../hardware/electronics/kicad/cuty_carrier/README.md) (KiCad 7 project, Gerbers for PCBWay, BOM, schematic PDF).

Links on the board: Raspberry Pi 5 ↔ STM32 UART (Pi TX pin 8 → PA3, PA2 → Pi RX pin 10); STM32 PB6–PB9 and PA8 → five MG996R at 6 V; Pi header → Display-G 26-pin and ReSpeaker 2-Mics HAT (same physical pin numbering); LiPo 3S → fuses → servo buck (6 V) and Pi regulator (5.1 V USB-C). Power ground (PGND) and logic ground (GND) meet only at net tie NT1.

Still to validate on hardware: Black Pill row orientation against the real module, Pi 5 UART configuration, speaker output on the ReSpeaker, and the second (5.1 V / 5 A) regulator, which has not been bought yet. The board protects with fuses only; the LiPo still needs an over-discharge alarm/BMS and a balance charger.
