# C.U.T.Y Electronics

KiCad is the PCB source-of-truth area. `kicad/` contains the carrier project and its `fab/` exports; `schematics/` and `datasheets/` remain available for additional exports and component references.

The carrier v1.1 documents the STM32F401 Black Pill, Raspberry UART connection, servo connectors, future IMU connector, display/audio and power distribution. The design exists; fabrication, assembly, electrical validation and matching firmware remain pending. Coordinate wiring, rails and grounding with [wiring](../../docs/wiring.md) before hardware integration.


## Carrier board v1.1

[`kicad/cuty_carrier`](kicad/cuty_carrier/README.md): 2-layer, 100 × 92 mm carrier for Raspberry Pi 5, STM32F401 Black Pill, Display-G, ReSpeaker and five servo connectors. Native KiCad files, Gerbers, BOM, schematic PDF and previews are in that project. The saved DRC report lists 50 silkscreen warnings, zero severity-error entries and zero unconnected pads; this is a saved report, not a new hardware validation.
