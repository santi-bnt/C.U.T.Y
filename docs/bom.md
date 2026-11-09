# Bill of Materials — as built (Nov 2026)

What the robot is actually built from: the carrier PCB, two small orders (Mouser, Amazon México) and parts the team already owned. Printed parts and screws per step are in [hardware/cad/carcasa_v17/LEEME.md](../hardware/cad/carcasa_v17/LEEME.md).

## Carrier PCB — JLCPCB

| Item | Qty | Notes |
| --- | --- | --- |
| C.U.T.Y carrier v1.1, THT assembly | 1 | 37 parts soldered; order files and placement fixes in [fab/jlcpcb](../hardware/electronics/kicad/cuty_carrier/fab/jlcpcb/LEEME_JLCPCB.md) |

## Mouser México

| Item | Qty | Role |
| --- | --- | --- |
| Keystone 3568 mini blade fuse holder | 2 | F1, F2 (hand-soldered) |
| Mini blade fuse 10 A | 2 | F1, servo rail (one spare) |
| Mini blade fuse 5 A | 2 | F2, Raspberry Pi rail (one spare) |
| 2.54 mm jumper shunt | 1 | JP1, 5 V to the Black Pill |

## Amazon México

| ASIN | Item | Role |
| --- | --- | --- |
| B0CPJGHMPR | STM32F401CCU6 Black Pill | Servo/body controller on U1 |
| B0D1G4C28P | XL4015 5 A adjustable buck | 6 V servo rail (J4 → J5) |
| B0G5L9RR8C | 12 V → 5 V 5 A 25 W converter, USB-C lead | Raspberry Pi 5 supply (J6) |
| B07SXVKMQR | Round rocker switch 12 V 20 A (2-pack) | Main (J2) and servo (J3) switches |
| B09CT5VGPW | XT60 male-female extension 30 cm (2-pack) | Battery → J1 |
| B0GDYXF66D | Silicone wire 16 AWG, red/black | Switches and buck wiring |
| B07F128VSW | 40-way IDC ribbon, female-female | J12 → Pi 5 GPIO |
| B0CVS264R1 | Pi 5 CSI cable 22 → 15 pin, 50 cm | Camera |
| B0G4L68WHY | Taiss self-tapping screws M2/M3/M4 (685 pcs) | Everything into plastic |
| B07CBZRXQ8 | M3 hex socket screws + nuts (280 pcs) | Servo horns/cranks (into metal) |
| B07Z1MDC7H | Hobbypark M3 rod ends | Gimbal push-rods |
| B0D22QGKHN | M3 × 150 threaded rod (10 pcs) | Gimbal push-rods, cut to length |
| B0B9VKV5N9 | Silicone bumpers | Feet |

## Already owned by the team (measured)

| Item | Measured (mm) | Notes |
| --- | --- | --- |
| Raspberry Pi 5 + Active Cooler | 90.3 × 56 × 18 | incl. ports and micro SD |
| Display-G 3.5" SPI touch (waveshare35a driver) | 85 × 55.3 × 5.8 | 26-pin header to J13 with Dupont wires |
| ReSpeaker 2-Mics Pi HAT V2.0 | 65.5 × 29.8 × 11.5 | plugs into J14 |
| Arducam OV5647 5 MP | 24.4 × 23.3, 7.2 deep | held by a cradle in the visor |
| Speaker 2 W / 8 Ω | 35.4 × 25 × 5.5 | to the ReSpeaker speaker port |
| 5 × MG996R | 40.7 × 19.7 × 37 | head, two arms, two gimbal |
| LiPo 3S 11.1 V 2200 mAh 50C (HM2202) + balance charger | to measure | drawer fits up to 109 × 35 × 25 |
| Dupont wires, ≈0.85 kg PLA | | |
