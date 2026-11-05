# C.U.T.Y Electronics

KiCad is the PCB source-of-truth area. `kicad/` will hold native projects/boards; `schematics/` holds documented schematic exports; `datasheets/` holds reference documents with their component/version identity.

Plan areas for STM32 control PCB, Raspberry UART connection, servo connectors, IMU, and power distribution. The carrier PCB v1.0 (below) implements the UART, servo, display/audio and power-distribution design. Coordinate approved wiring, rails, and grounding with [wiring](../../docs/wiring.md) before hardware integration.


## Carrier board v1.1

[`kicad/cuty_carrier`](kicad/cuty_carrier/README.md): 2-layer, 100 × 92 mm carrier for Raspberry Pi 5, Black Pill, Display-G, ReSpeaker and 5 servos. Gerbers ready for PCBWay in `kicad/cuty_carrier/fab/`; turnkey assembly files (BOM with manufacturer part numbers, centroid, assembly drawing and order steps) in [`kicad/cuty_carrier/fab/pcba/`](kicad/cuty_carrier/fab/pcba/LEEME_PCBA.md).
