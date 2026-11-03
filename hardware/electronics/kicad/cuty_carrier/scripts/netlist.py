"""Single source of truth for the C.U.T.Y carrier board.

Both the schematic (gen_sch.py) and the PCB (gen_pcb.py) are generated from
this table, so they cannot drift apart. Pin numbers follow the KiCad symbol /
footprint numbering. Raspberry Pi, display and ReSpeaker headers all use the
physical Raspberry Pi 40-pin numbering, as in the project's wiring tables.
"""

from __future__ import annotations

from dataclasses import dataclass, field

FP = "/usr/share/kicad/footprints/"
R_FP = ("Resistor_THT", "R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal")
TB_FP = ("TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal")
LED_FP = ("LED_THT", "LED_D3.0mm")


@dataclass
class Part:
    ref: str
    value: str
    symbol: str                   # "Lib:Name" in the KiCad symbol libraries (or "CUTY:...")
    footprint: tuple[str, str]    # (library, footprint)
    pins: dict[str, str]          # pin number -> net name ("" = not connected)
    note: str = ""                # Silkscreen / BOM hint
    mpn: str = ""                 # Suggested part to buy
    group: str = ""
    dnp: bool = False
    extra: dict = field(default_factory=dict)


# --------------------------------------------------------------------------
# Raspberry Pi 5 40-pin header (physical numbering) -> net
# --------------------------------------------------------------------------
PI_GND = (6, 9, 14, 20, 25, 30, 34, 39)
PI_HEADER: dict[int, str] = {
    1: "+3V3", 2: "+5V", 3: "I2C1_SDA", 4: "+5V", 5: "I2C1_SCL",
    7: "AUD_MCLK", 8: "PI_TXD", 10: "PI_RXD", 11: "TP_IRQ", 12: "I2S_BCLK",
    17: "+3V3", 18: "LCD_DC", 19: "SPI0_MOSI", 21: "SPI0_MISO", 22: "LCD_RST",
    23: "SPI0_SCLK", 24: "LCD_CS", 26: "TP_CS", 35: "I2S_LRCLK",
    37: "AUD_RST", 38: "I2S_DIN", 40: "I2S_DOUT",
    **{p: "GND" for p in PI_GND},
}
# Pins of each plug-in header that are wired (others stay unconnected).
DISPLAY_USED = (1, 2, 4, 6, 9, 11, 14, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26)
RESPEAKER_USED = (1, 2, 3, 4, 5, 6, 7, 9, 12, 14, 17, 20, 25, 30, 34, 35, 37, 38, 39, 40)
RESPEAKER_MUST_BE_OPEN = (11, 19, 23, 32, 33)

# --------------------------------------------------------------------------
# WeAct Black Pill STM32F401CCU6 (two 1x20 rows, 15.24 mm apart)
# Pins 1..20: row with PB12 at the USB-C end; 21..40: row with VBAT at the USB-C end.
# --------------------------------------------------------------------------
BP_ROW_A = ["PB12", "PB13", "PB14", "PB15", "PA8", "PA9", "PA10", "PA11", "PA12", "PA15",
            "PB3", "PB4", "PB5", "PB6", "PB7", "PB8", "PB9", "5V", "GND", "3V3"]
BP_ROW_B = ["VBAT", "PC13", "PC14", "PC15", "NRST", "PA0", "PA1", "PA2", "PA3", "PA4",
            "PA5", "PA6", "PA7", "PB0", "PB1", "PB2", "PB10", "3V3", "GND", "5V"]
BP_NAMES = {str(i + 1): n for i, n in enumerate(BP_ROW_A)} | {str(i + 21): n for i, n in enumerate(BP_ROW_B)}
BP_NET_BY_NAME = {
    "PB6": "PWM1", "PB7": "PWM2", "PB8": "PWM3", "PB9": "PWM4", "PA8": "PWM5",
    "PA2": "PI_RXD", "PA3": "PI_TXD",         # USART2: PA2=TX -> Pi RX, PA3=RX <- Pi TX
    "PA0": "VBAT_SENSE",
    "PB10": "I2C2_SCL", "PB3": "I2C2_SDA",
    "5V": "+5V_BP", "3V3": "+3V3_BP", "GND": "GND",
}
SERVO_NAMES = ["Cabeza", "Brazo izq", "Brazo der", "Base 1", "Base 2"]


def build() -> list[Part]:
    parts: list[Part] = []
    add = parts.append

    # ---------------- Power entry and distribution ----------------------
    add(Part("J1", "XT60 BAT 3S", "Connector_Generic:Conn_01x02",
             ("Connector_AMASS", "AMASS_XT60PW-M_1x02_P7.20mm_Horizontal"),
             {"1": "PGND", "2": "VBAT_RAW"}, "Bateria LiPo 3S", "AMASS XT60PW-M", "power"))
    add(Part("J2", "SW PRINCIPAL", "Connector_Generic:Conn_01x02", TB_FP,
             {"1": "VBAT_SW", "2": "VBAT_RAW"}, "A interruptor general (>=10 A)", "Phoenix MKDS 1,5/2-5,08", "power"))
    add(Part("F1", "10A", "Device:Fuse", ("Fuse", "Fuseholder_Blade_Mini_Keystone_3568"),
             {"1": "VBAT_SW", "2": "VBAT_SERVO"}, "Fusible servos (mini blade 10 A)", "Keystone 3568 + fusible mini 10 A", "power"))
    add(Part("F2", "5A", "Device:Fuse", ("Fuse", "Fuseholder_Blade_Mini_Keystone_3568"),
             {"1": "VBAT_SW", "2": "VBAT_PI"}, "Fusible Raspberry (mini blade 5 A)", "Keystone 3568 + fusible mini 5 A", "power"))
    add(Part("J3", "SW SERVOS", "Connector_Generic:Conn_01x02", TB_FP,
             {"1": "VBAT_SERVO", "2": "VBAT_SERVO_SW"}, "A interruptor de servos", "Phoenix MKDS 1,5/2-5,08", "power"))
    add(Part("J4", "BUCK IN", "Connector_Generic:Conn_01x02", TB_FP,
             {"1": "VBAT_SERVO_SW", "2": "PGND"}, "Entrada del buck de servos", "Phoenix MKDS 1,5/2-5,08", "power"))
    add(Part("J5", "BUCK OUT 6V", "Connector_Generic:Conn_01x02", TB_FP,
             {"1": "PGND", "2": "+6V_SERVO"}, "Salida del buck ajustado a 6 V", "Phoenix MKDS 1,5/2-5,08", "power"))
    add(Part("J6", "REG RPI", "Connector_Generic:Conn_01x02", TB_FP,
             {"1": "VBAT_PI", "2": "PGND"}, "Entrada del regulador 5.1 V / 5 A (USB-C a Pi 5)", "Phoenix MKDS 1,5/2-5,08", "power"))
    add(Part("NT1", "NetTie", "Device:NetTie_2", ("NetTie", "NetTie-2_THT_Pad1.0mm"),
             {"1": "GND", "2": "PGND"}, "Union unica tierra logica / potencia", "", "power"))
    for ref in ("C1", "C2"):
        add(Part(ref, "1000uF 16V", "Device:C_Polarized", ("Capacitor_THT", "CP_Radial_D10.0mm_P5.00mm"),
                 {"1": "+6V_SERVO", "2": "PGND"}, "Bulk servos", "Electrolitico 1000 uF 16 V low-ESR D10 P5", "servo"))
    add(Part("R9", "1k", "Device:R", R_FP, {"1": "+6V_SERVO", "2": "LED_6V"}, "", "Resistencia 1/4 W", "power"))
    add(Part("D3", "6V", "Device:LED", LED_FP, {"1": "PGND", "2": "LED_6V"}, "LED servos", "LED 3 mm azul", "power"))
    add(Part("R10", "4.7k", "Device:R", R_FP, {"1": "VBAT_SW", "2": "LED_BAT"}, "", "Resistencia 1/4 W", "power"))
    add(Part("D4", "BAT", "Device:LED", LED_FP, {"1": "PGND", "2": "LED_BAT"}, "LED bateria", "LED 3 mm rojo", "power"))

    # ---------------- Servos ------------------------------------------
    for i in range(5):
        n = i + 1
        add(Part(f"R{n}", "220", "Device:R", R_FP, {"1": f"PWM{n}", "2": f"SERVO{n}"},
                 "Serie PWM", "Resistencia 1/4 W", "servo"))
        add(Part(f"J{6 + n}", f"SERVO{n}", "Connector_Generic:Conn_01x03",
                 ("Connector_PinHeader_2.54mm", "PinHeader_1x03_P2.54mm_Vertical"),
                 {"1": f"SERVO{n}", "2": "+6V_SERVO", "3": "PGND"},
                 f"MG996R {SERVO_NAMES[i]} (S + -)", "Tira de pines 1x3 2.54 mm", "servo"))

    # ---------------- Raspberry Pi and its plug-in boards ---------------
    add(Part("J12", "RPI5 GPIO", "Connector_Generic:Conn_02x20_Odd_Even",
             ("Connector_IDC", "IDC-Header_2x20_P2.54mm_Vertical"),
             {str(p): PI_HEADER.get(p, "") for p in range(1, 41)},
             "Cable plano 40 vias a la Raspberry Pi 5", "Box header 2x20 2.54 mm", "logic"))
    add(Part("J13", "PANTALLA 3.5", "Connector_Generic:Conn_02x13_Odd_Even",
             ("Connector_PinHeader_2.54mm", "PinHeader_2x13_P2.54mm_Vertical"),
             {str(p): (PI_HEADER.get(p, "") if p in DISPLAY_USED else "") for p in range(1, 27)},
             "Display-G 26 pines (waveshare35a)", "Tira de pines 2x13 2.54 mm", "logic"))
    add(Part("J14", "RESPEAKER", "Connector_Generic:Conn_02x20_Odd_Even",
             ("Connector_PinHeader_2.54mm", "PinHeader_2x20_P2.54mm_Vertical"),
             {str(p): (PI_HEADER.get(p, "") if p in RESPEAKER_USED else "") for p in range(1, 41)},
             "ReSpeaker 2-Mics Pi HAT V2.0", "Tira de pines 2x20 2.54 mm", "logic"))

    # ---------------- STM32 Black Pill ---------------------------------
    add(Part("U1", "BlackPill F401CC", "CUTY:WeAct_BlackPill",
             ("CUTY", "WeAct_BlackPill_Socket"),
             {num: BP_NET_BY_NAME.get(name, "") for num, name in BP_NAMES.items()},
             "WeAct Black Pill STM32F401CCU6", "2x zocalo hembra 1x20 2.54 mm", "logic"))
    add(Part("JP1", "5V STM32", "Connector_Generic:Conn_01x02",
             ("Connector_PinHeader_2.54mm", "PinHeader_1x02_P2.54mm_Vertical"),
             {"1": "+5V", "2": "5V_JP"}, "Puente: 5 V de la Pi a la Black Pill", "Tira 1x2 + jumper", "logic"))
    add(Part("D1", "1N5819", "Device:D_Schottky", ("Diode_THT", "D_DO-41_SOD81_P10.16mm_Horizontal"),
             {"1": "+5V_BP", "2": "5V_JP"}, "Evita retroalimentar 5 V desde el USB", "1N5819", "logic"))
    add(Part("R6", "100k", "Device:R", R_FP, {"1": "VBAT_SW", "2": "VBAT_SENSE"}, "Divisor bateria", "Resistencia 1/4 W 1%", "logic"))
    add(Part("R7", "22k", "Device:R", R_FP, {"1": "VBAT_SENSE", "2": "GND"}, "Divisor bateria", "Resistencia 1/4 W 1%", "logic"))
    add(Part("C3", "100nF", "Device:C", ("Capacitor_THT", "C_Disc_D5.0mm_W2.5mm_P5.00mm"),
             {"1": "VBAT_SENSE", "2": "GND"}, "Filtro ADC", "Ceramico 100 nF 50 V", "logic"))
    add(Part("R8", "1k", "Device:R", R_FP, {"1": "+5V", "2": "LED_5V"}, "", "Resistencia 1/4 W", "logic"))
    add(Part("D2", "5V", "Device:LED", LED_FP, {"1": "GND", "2": "LED_5V"}, "LED 5 V Pi", "LED 3 mm verde", "logic"))
    add(Part("J15", "I2C IMU", "Connector_Generic:Conn_01x04",
             ("Connector_PinHeader_2.54mm", "PinHeader_1x04_P2.54mm_Vertical"),
             {"1": "+3V3_BP", "2": "GND", "3": "I2C2_SCL", "4": "I2C2_SDA"},
             "IMU futura en I2C2 de la STM32", "Tira de pines 1x4 2.54 mm", "logic"))
    add(Part("R11", "4.7k", "Device:R", R_FP, {"1": "+3V3_BP", "2": "I2C2_SCL"}, "Pull-up I2C", "Resistencia 1/4 W", "logic"))
    add(Part("R12", "4.7k", "Device:R", R_FP, {"1": "+3V3_BP", "2": "I2C2_SDA"}, "Pull-up I2C", "Resistencia 1/4 W", "logic"))

    # ---------------- Mechanical -----------------------------------------
    for n in range(1, 5):
        add(Part(f"H{n}", "M3", "Mechanical:MountingHole", ("MountingHole", "MountingHole_3.2mm_M3"),
                 {}, "Tornillo M3", "", "mech"))
    return parts


POWER_NETS = {"VBAT_RAW", "VBAT_SW", "VBAT_SERVO", "VBAT_SERVO_SW", "VBAT_PI", "+6V_SERVO", "PGND"}
SUPPLY_NETS = {"+5V", "+3V3", "+5V_BP", "5V_JP", "+3V3_BP", "GND"}


def nets(parts: list[Part]) -> dict[str, list[tuple[str, str]]]:
    out: dict[str, list[tuple[str, str]]] = {}
    for p in parts:
        for pin, net in p.pins.items():
            if net:
                out.setdefault(net, []).append((p.ref, pin))
    return out


def check(parts: list[Part]) -> None:
    """Design-rule sanity checks on the connection table itself."""
    by_ref = {p.ref: p for p in parts}
    assert len(by_ref) == len(parts), "duplicate reference"
    n = nets(parts)
    for net, members in n.items():
        assert len(members) >= 2, f"net {net} has a single pin: {members}"
    # Display and ReSpeaker pins are the same physical Pi pins.
    for hdr, used in (("J13", DISPLAY_USED), ("J14", RESPEAKER_USED)):
        for pin in used:
            assert by_ref[hdr].pins[str(pin)] == by_ref["J12"].pins[str(pin)], (hdr, pin)
    for pin in RESPEAKER_MUST_BE_OPEN:
        assert by_ref["J14"].pins[str(pin)] == "", pin
    assert by_ref["J14"].pins["8"] == by_ref["J14"].pins["10"] == ""   # UART stays off the HAT
    # 3.3 V and 5 V rails never touch; regulators are never paralleled.
    for a, b in (("+3V3", "+5V"), ("+3V3", "+3V3_BP"), ("+5V", "+5V_BP")):
        assert not set(n[a]) & set(n[b])
    # Servos only on the 6 V rail and power ground.
    for i in range(7, 12):
        assert by_ref[f"J{i}"].pins["2"] == "+6V_SERVO" and by_ref[f"J{i}"].pins["3"] == "PGND"
    # UART crossover.
    assert by_ref["J12"].pins["8"] == "PI_TXD" and BP_NET_BY_NAME["PA3"] == "PI_TXD"
    assert by_ref["J12"].pins["10"] == "PI_RXD" and BP_NET_BY_NAME["PA2"] == "PI_RXD"


if __name__ == "__main__":
    ps = build()
    check(ps)
    for net, members in sorted(nets(ps).items()):
        print(f"{net:14s} {len(members):2d}  {' '.join(f'{r}.{p}' for r, p in members)}")
