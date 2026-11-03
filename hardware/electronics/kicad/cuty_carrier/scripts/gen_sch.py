"""Generate cuty_carrier.kicad_sch (KiCad 7) from netlist.py.

Every connected pin gets a short wire stub and a net label; unconnected pins
get a no-connect flag. Symbols come from the stock KiCad libraries plus the
project's CUTY.kicad_sym, embedded in the schematic as KiCad does itself.
"""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

import sexpdata
from sexpdata import Symbol

from netlist import Part, SERVO_NAMES, build, check

ROOT = Path(__file__).resolve().parents[1]
SYMDIR = Path("/usr/share/kicad/symbols")
PROJECT = "cuty_carrier"
ROOT_UUID = str(uuid.uuid5(uuid.NAMESPACE_URL, "cuty_carrier/root"))
STUB = 2.54


def uid(*key: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "cuty_carrier/" + "/".join(key)))


def f(v: float) -> str:
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ---------------------------------------------------------------- library
_lib_cache: dict[str, list] = {}


def load_symbol(lib_id: str) -> list:
    lib, name = lib_id.split(":")
    if lib not in _lib_cache:
        path = ROOT / "CUTY.kicad_sym" if lib == "CUTY" else SYMDIR / f"{lib}.kicad_sym"
        _lib_cache[lib] = sexpdata.loads(path.read_text())
    for node in _lib_cache[lib]:
        if isinstance(node, list) and node and node[0] == Symbol("symbol") and node[1] == name:
            return node
    raise KeyError(lib_id)


def pins_of(sym: list) -> dict[str, tuple[float, float, int]]:
    """pin number -> (x, y, angle) in symbol coordinates (y up)."""
    out = {}

    def walk(node):
        if not isinstance(node, list):
            return
        if node and node[0] == Symbol("pin"):
            at = next(n for n in node if isinstance(n, list) and n[0] == Symbol("at"))
            num = next(n for n in node if isinstance(n, list) and n[0] == Symbol("number"))
            out[str(num[1])] = (float(at[1]), float(at[2]), int(at[3]))
            return
        for child in node:
            walk(child)

    walk(sym)
    return out


def embedded(lib_id: str) -> str:
    sym = load_symbol(lib_id)
    copy = list(sym)
    copy[1] = lib_id
    return sexpdata.dumps(copy)


# ---------------------------------------------------------------- layout
# Symbol anchor positions on an A3 sheet (mm), chosen per group.
def layout(parts: list[Part]) -> dict[str, tuple[float, float, int]]:
    pos: dict[str, tuple[float, float, int]] = {}
    g = 2.54

    def snap(v):
        return round(v / 1.27) * 1.27

    row1 = ["J1", "J2", "F1", "F2", "J3", "J4", "J5", "J6", "NT1"]
    for i, r in enumerate(row1):
        pos[r] = (snap(30 + i * 24), snap(62), 0)
    for i, r in enumerate(["C1", "C2", "R9", "D3", "R10", "D4"]):
        pos[r] = (snap(30 + i * 24), snap(104), 0)
    for i in range(5):
        pos[f"J{7 + i}"] = (snap(30 + i * 34), snap(142), 0)
        pos[f"R{i + 1}"] = (snap(30 + i * 34), snap(172), 0)
    pos["J12"] = (snap(265), snap(85), 0)
    pos["J13"] = (snap(345), snap(70), 0)
    pos["J14"] = (snap(345), snap(160), 0)
    pos["U1"] = (snap(265), snap(222), 0)
    for i, r in enumerate(["JP1", "D1", "R6", "R7", "C3", "R8", "D2"]):
        pos[r] = (snap(30 + i * 24), snap(228), 0)
    pos["J15"] = (snap(30), snap(270), 0)
    pos["R11"] = (snap(62), snap(270), 0)
    pos["R12"] = (snap(86), snap(270), 0)
    for i in range(4):
        pos[f"H{i + 1}"] = (snap(330 + i * 15), snap(240), 0)
    missing = {p.ref for p in parts} - set(pos)
    assert not missing, missing
    return pos


TEXTS = [
    (20, 30, "ALIMENTACION: Bateria 3S -> J2 interruptor general -> F1 (10 A) -> J3 interruptor servos -> J4/J5 buck 6 V -> servos", 1.8),
    (20, 35, "                                                      -> F2 (5 A) -> J6 regulador 5.1 V / 5 A con salida USB-C a la Raspberry Pi 5", 1.8),
    (20, 40, "PGND (potencia) y GND (logica) se unen SOLO en NT1, junto a J1.", 1.8),
    (20, 124, "SERVOMOTORES MG996R (S, V+, GND) a 6 V. Senal PWM desde la Black Pill con 220 ohm en serie.", 1.8),
    (232, 30, "RASPBERRY PI 5 (cable plano 40 vias), PANTALLA Display-G 26 pines y ReSpeaker 2-Mics HAT V2.0", 1.8),
    (232, 35, "J13 y J14 replican la numeracion fisica de la Pi; solo se cablean los pines indicados.", 1.8),
    (232, 40, "ReSpeaker: pines 8, 10, 11, 19, 23, 32, 33 y libres sin conectar.", 1.8),
    (20, 198, "STM32F401 BLACK PILL: UART2 PA2 TX -> Pi RX (pin 10), PA3 RX <- Pi TX (pin 8). 5 V desde la Pi por JP1 + D1.", 1.8),
    (20, 203, "La 3.3 V de la Black Pill (+3V3_BP) NO se une a la 3.3 V de la Pi. PA1 mide la bateria: Vbat * 22k / 122k.", 1.8),
    (100, 268, "I2C2 para IMU futura (PB10 SCL, PB3 SDA).", 1.8),
]


def text_item(x, y, s, size):
    return (f'(text "{s}" (at {f(x)} {f(y)} 0) (effects (font (size {size} {size})) (justify left bottom)) '
            f'(uuid {uid("text", s)}))')


def main() -> None:
    parts = build()
    check(parts)
    pos = layout(parts)
    lib_ids = sorted({p.symbol for p in parts})
    out: list[str] = []
    out.append(f'(kicad_sch (version 20230121) (generator eeschema)\n\n  (uuid {ROOT_UUID})\n\n  (paper "A3")\n')
    out.append('  (title_block (title "C.U.T.Y - Placa base (carrier)") (date "2026-11-02") (rev "1.0")\n'
               '    (company "Tec de Monterrey - Campus Guadalajara")\n'
               '    (comment 1 "Raspberry Pi 5 + STM32F401 Black Pill + Display-G 3.5in + ReSpeaker 2-Mics + 5x MG996R")\n'
               '    (comment 2 "Generado desde scripts/netlist.py"))\n')
    out.append("  (lib_symbols\n" + "\n".join("    " + embedded(l) for l in lib_ids) + "\n  )\n")

    for x, y, s, size in TEXTS:
        out.append("  " + text_item(x, y, s, size))

    for p in parts:
        x, y, rot = pos[p.ref]
        sym = load_symbol(p.symbol)
        pins = pins_of(sym)
        fp = f"{p.footprint[0]}:{p.footprint[1]}"
        # Reference above, value below the symbol's extent.
        ys = [py for _, py, _ in pins.values()] or [0]
        top, bot = y - max(ys) - 3.5, y - min(ys) + 3.5
        if not pins:
            top, bot = y - 4, y + 4
        right_side = any(a == 180 for _, _, a in pins.values())
        tx = x if right_side or not pins else x + 3
        out.append(f'''  (symbol (lib_id "{p.symbol}") (at {f(x)} {f(y)} {rot}) (unit 1)
    (in_bom {"no" if p.group == "mech" or p.symbol == "Device:NetTie_2" else "yes"}) (on_board yes) (dnp no)
    (uuid {uid("sym", p.ref)})
    (property "Reference" "{p.ref}" (at {f(tx)} {f(top)} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "{p.value}" (at {f(tx)} {f(bot)} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "{fp}" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "~" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Descripcion" "{p.note}" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Compra" "{p.mpn}" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) hide))''')
        for num in pins:
            out.append(f'    (pin "{num}" (uuid {uid("pin", p.ref, num)}))')
        out.append(f'    (instances (project "{PROJECT}" (path "/{ROOT_UUID}" (reference "{p.ref}") (unit 1))))\n  )')

        for num, (px, py, ang) in pins.items():
            cx, cy = x + px, y - py                    # symbol y-up -> sheet y-down
            # Direction pointing away from the symbol body.
            dx, dy = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[ang]
            net = p.pins.get(num, "")
            if not net:
                out.append(f'  (no_connect (at {f(cx)} {f(cy)}) (uuid {uid("nc", p.ref, num)}))')
                continue
            ex, ey = cx + dx * STUB, cy + dy * STUB
            out.append(f'  (wire (pts (xy {f(cx)} {f(cy)}) (xy {f(ex)} {f(ey)})) (stroke (width 0) (type default)) (uuid {uid("w", p.ref, num)}))')
            angle, just = {(-1, 0): (180, "right bottom"), (1, 0): (0, "left bottom"),
                           (0, 1): (270, "right bottom"), (0, -1): (90, "left bottom")}[(dx, dy)]
            out.append(f'  (label "{net}" (at {f(ex)} {f(ey)} {angle}) (fields_autoplaced) '
                       f'(effects (font (size 1.27 1.27)) (justify {just})) (uuid {uid("lbl", p.ref, num)}))')

    out.append(f'\n  (sheet_instances (path "/" (page "1")))\n)\n')
    (ROOT / f"{PROJECT}.kicad_sch").write_text("\n".join(out))

    # Symbol UUIDs for the PCB generator (footprint <-> symbol links).
    (ROOT / "scripts" / "symbol_uuids.json").write_text(
        json.dumps({p.ref: uid("sym", p.ref) for p in parts}, indent=1))
    print("schematic written:", len(parts), "symbols")


if __name__ == "__main__":
    main()
