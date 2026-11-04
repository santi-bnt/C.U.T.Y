# Bill of Materials — Hardware and Design Status

This summary distinguishes reported hardware from the carrier design; it is not a completed purchasing or assembly record. The detailed carrier component list is [fab/cuty_carrier_BOM.csv](../hardware/electronics/kicad/cuty_carrier/fab/cuty_carrier_BOM.csv).

| Area | Hardware / design | Quantity | Status |
| --- | --- | --- | --- |
| Compute | Raspberry Pi 5 | 1 | Current platform; basic voice, screen and camera startup tested; stability validation pending |
| Control | STM32F401 Black Pill | 1 | Current control board; firmware and exact MCU suffix/board revision still to document |
| Audio | ReSpeaker 2-Mics Pi HAT V2.0 and passive speaker (2 W / 8 ohm) | 1 each | Capture and playback tested on the Pi; output levels and noise investigated separately |
| Display | Display-G 3.5-inch SPI touchscreen, 480 × 320, ADS7846 | 1 | Existing working wiring retained; intermittent white-screen issue unresolved |
| Vision | Raspberry Pi camera, OV5647 reported by libcamera | 1 | Camera initialization observed; face detection and gaze tracking implemented, physical validation pending |
| Carrier | C.U.T.Y carrier PCB v1.1 | 1 in design | KiCad, Gerbers, BOM and exports present; fabrication, assembly and electrical validation pending |
| Motion | MG996R servo connectors | 5 in carrier design | PWM firmware, mechanical loads, calibration and physical integration pending |
| Power | LiPo 3S, 6 V servo buck, 5.1 V / 5 A Pi supply and protection | See carrier BOM | Carrier design only; confirm actual parts, power budget and assembly before use |
| Feedback | IMU | TBD | I2C connector in carrier design; sensor selection and firmware pending |

Record actual part numbers, revisions, quantities, voltage/current ratings, mechanical fit, sources and costs as hardware is acquired and validated.
