"""Project library: WeAct Black Pill symbol and socket footprint.

Geometry follows the WeAct MiniF4 (Black Pill) official STEP model as audited
by github.com/hojoonch/BlackPill_WeAct-BlackPill-STM32F411CEU6-KiCad-Library
(validation/pinout_and_geometry.csv). Top view, USB-C on the LEFT:
  * pads 1..20  (PB12 ... 3V3) on the LOWER row, PB12 next to the USB-C;
  * pads 21..40 (VBAT ... 5V)  on the UPPER row, DIP numbering: VBAT at the far
    end, 5V next to the USB-C;
  * row spacing 15.2146 mm, pitch 2.54 mm; SWD header (3V3 SWDIO SWCLK GND) at
    the far end, given clearance holes here.
F401CC and F411CE Black Pills (V2.0+) share this pinout and outline.
"""

from __future__ import annotations

from pathlib import Path

from netlist import BP_NAMES

ROOT = Path(__file__).resolve().parents[1]
PITCH = 2.54
ROW_A_Y = 6.4008        # pads 1..20
ROW_B_Y = -8.8138       # pads 21..40
X0 = -18.161            # pad 1 and pad 40 (USB-C end)
BOARD = (-19.558, -11.5852, 33.252, 9.1948)   # module outline x0, y0, x1, y1
SWD_X, SWD_Y = 26.3144, (2.5654, 0.0254, -2.5146, -5.0546)


def f(v: float) -> str:
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def pad_xy(num: int) -> tuple[float, float]:
    if num <= 20:
        return X0 + (num - 1) * PITCH, ROW_A_Y
    return X0 + (40 - num) * PITCH, ROW_B_Y


def symbol() -> str:
    font = "(effects (font (size 1.27 1.27)))"
    pins = []
    for i in range(20):
        y = 24.13 - i * PITCH
        pins.append(f'(pin passive line (at -12.7 {f(y)} 0) (length 2.54) (name "{BP_NAMES[str(i + 1)]}" {font}) (number "{i + 1}" {font}))')
        # Right side top-to-bottom shows 40..21 so it reads like the module.
        pins.append(f'(pin passive line (at 12.7 {f(y)} 180) (length 2.54) (name "{BP_NAMES[str(40 - i)]}" {font}) (number "{40 - i}" {font}))')
    return f'''(symbol "WeAct_BlackPill" (in_bom yes) (on_board yes)
  (property "Reference" "U" (at 0 27.94 0) {font})
  (property "Value" "WeAct_BlackPill" (at 0 -27.94 0) {font})
  (property "Footprint" "CUTY:WeAct_BlackPill_Socket" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "https://github.com/WeActStudio/WeActStudio.MiniSTM32F4x1" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (property "ki_description" "WeAct Black Pill STM32F401/F411 en zocalos 1x20, numeracion DIP oficial: 1 = PB12 (junto al USB-C) ... 20 = 3V3; 21 = VBAT ... 40 = 5V (junto al USB-C)." (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (symbol "WeAct_BlackPill_0_1"
    (rectangle (start -10.16 26.67) (end 10.16 -26.67) (stroke (width 0.254) (type default)) (fill (type background))))
  (symbol "WeAct_BlackPill_1_1"
    {chr(10).join("    " + p for p in pins)}))'''


def write_symbol_lib() -> None:
    (ROOT / "CUTY.kicad_sym").write_text(
        f"(kicad_symbol_lib (version 20220914) (generator cuty_gen)\n{symbol()}\n)\n")


def write_footprint() -> None:
    sk = "(stroke (width 0.12) (type solid))"
    x0, y0, x1, y1 = BOARD
    cy = (y0 + y1) / 2
    lines = [
        '(footprint "WeAct_BlackPill_Socket" (version 20221018) (generator cuty_gen) (layer "F.Cu")',
        '  (descr "WeAct Black Pill (STM32F401/F411, V2.0+) en dos zocalos hembra 1x20 2.54 mm. Vista superior con USB-C a la izquierda: pads 1-20 (PB12..3V3) fila inferior, PB12 junto al USB; pads 21-40 (VBAT..5V) fila superior, 5V junto al USB. Filas a 15.2146 mm. Geometria del STEP oficial de WeAct.")',
        '  (tags "STM32 BlackPill WeAct MiniF4 socket")',
        '  (attr through_hole)',
        f'  (fp_text reference "REF**" (at {f((x0 + x1) / 2)} {f(cy)}) (layer "F.SilkS") (effects (font (size 1.2 1.2) (thickness 0.18))))',
        f'  (fp_text value "WeAct_BlackPill_Socket" (at {f((x0 + x1) / 2)} {f(y1 + 1.5)}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
        f'  (fp_rect (start {f(x0)} {f(y0)}) (end {f(x1)} {f(y1)}) (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))',
        f'  (fp_rect (start {f(x0 - 0.25)} {f(y0 - 0.25)}) (end {f(x1 + 0.25)} {f(y1 + 0.25)}) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))',
        # USB-C marker at the module end (inside the outline).
        f'  (fp_rect (start {f(x0 + 0.4)} {f(cy - 4.5)}) (end {f(x0 + 6.6)} {f(cy + 4.5)}) {sk} (fill none) (layer "F.SilkS"))',
        f'  (fp_text user "USB-C" (at {f(x0 + 3.5)} {f(cy)} 90) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
        f'  (fp_text user "SWD" (at {f(SWD_X - 2.2)} {f(sum(SWD_Y) / 4)} 90) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.13))))',
    ]
    for y in (ROW_A_Y, ROW_B_Y):
        lines.append(f'  (fp_rect (start {f(X0 - 1.33)} {f(y - 1.33)}) (end {f(X0 + 19 * PITCH + 1.33)} {f(y + 1.33)}) {sk} (fill none) (layer "F.SilkS"))')
    # Pin-1 marker next to PB12, outside the socket outline.
    px, py = pad_xy(1)
    lines.append(f'  (fp_poly (pts (xy {f(px - 1.9)} {f(py + 1.9)}) (xy {f(px - 0.9)} {f(py + 1.9)}) (xy {f(px - 1.9)} {f(py + 0.9)})) {sk} (fill solid) (layer "F.SilkS"))')
    for num in range(1, 41):
        x, y = pad_xy(num)
        shape = "rect" if num == 1 else "circle"
        lines.append(f'  (pad "{num}" thru_hole {shape} (at {f(x)} {f(y)}) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask"))')
        # Pin names between the rows: visible whenever the module is unplugged.
        ty = y - 3.0 if num <= 20 else y + 3.0
        lines.append(f'  (fp_text user "{BP_NAMES[str(num)]}" (at {f(x)} {f(ty)} 90) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.13))))')
    # Clearance holes in case the module's SWD header pins point down.
    for y in SWD_Y:
        lines.append(f'  (pad "" np_thru_hole circle (at {f(SWD_X)} {f(y)}) (size 1.3 1.3) (drill 1.3) (layers "*.Cu" "*.Mask"))')
    lines.append(")")
    out = ROOT / "CUTY.pretty"
    out.mkdir(exist_ok=True)
    (out / "WeAct_BlackPill_Socket.kicad_mod").write_text("\n".join(lines) + "\n")


def write_lib_tables() -> None:
    (ROOT / "sym-lib-table").write_text(
        '(sym_lib_table\n  (lib (name "CUTY")(type "KiCad")(uri "${KIPRJMOD}/CUTY.kicad_sym")(options "")(descr "C.U.T.Y project symbols"))\n)\n')
    (ROOT / "fp-lib-table").write_text(
        '(fp_lib_table\n  (lib (name "CUTY")(type "KiCad")(uri "${KIPRJMOD}/CUTY.pretty")(options "")(descr "C.U.T.Y project footprints"))\n)\n')


if __name__ == "__main__":
    write_symbol_lib()
    write_footprint()
    write_lib_tables()
    # Self-check against the audited WeAct geometry (pad: name, x, y).
    golden = {1: ("PB12", -18.161, 6.4008), 14: ("PB6", 14.859, 6.4008), 20: ("3V3", 30.099, 6.4008),
              21: ("VBAT", 30.099, -8.8138), 26: ("PA0", 17.399, -8.8138), 27: ("PA1", 14.859, -8.8138),
              28: ("PA2", 12.319, -8.8138), 37: ("PB10", -10.541, -8.8138), 40: ("5V", -18.161, -8.8138)}
    for num, (name, gx, gy) in golden.items():
        x, y = pad_xy(num)
        assert BP_NAMES[str(num)] == name and abs(x - gx) < 1e-3 and abs(y - gy) < 1e-3, (num, name, x, y)
    print("library written; Black Pill geometry matches the audited WeAct STEP")
