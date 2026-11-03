"""Project library: WeAct Black Pill symbol and socket footprint."""

from __future__ import annotations

from pathlib import Path

from netlist import BP_NAMES

ROOT = Path(__file__).resolve().parents[1]
ROW_PITCH = 15.24      # mm between the two 1x20 rows (0.6 in)
PITCH = 2.54
MODULE_L, MODULE_W = 52.81, 20.78


def f(v: float) -> str:
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def symbol() -> str:
    font = "(effects (font (size 1.27 1.27)))"
    pins = []
    for i in range(20):
        y = 24.13 - i * PITCH
        pins.append(f'(pin passive line (at -12.7 {f(y)} 0) (length 2.54) (name "{BP_NAMES[str(i + 1)]}" {font}) (number "{i + 1}" {font}))')
        pins.append(f'(pin passive line (at 12.7 {f(y)} 180) (length 2.54) (name "{BP_NAMES[str(i + 21)]}" {font}) (number "{i + 21}" {font}))')
    return f'''(symbol "WeAct_BlackPill" (in_bom yes) (on_board yes)
  (property "Reference" "U" (at 0 27.94 0) {font})
  (property "Value" "WeAct_BlackPill" (at 0 -27.94 0) {font})
  (property "Footprint" "CUTY:WeAct_BlackPill_Socket" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "https://stm32-base.org/boards/STM32F401CCU6-WeAct-Black-Pill-V1.2" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (property "ki_description" "WeAct Black Pill STM32F401CCU6 en zocalos 1x20. Pines 1-20: fila PB12 (PB12 en el extremo USB). Pines 21-40: fila VBAT (VBAT en el extremo USB)." (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (symbol "WeAct_BlackPill_0_1"
    (rectangle (start -10.16 26.67) (end 10.16 -26.67) (stroke (width 0.254) (type default)) (fill (type background))))
  (symbol "WeAct_BlackPill_1_1"
    {chr(10).join("    " + p for p in pins)}))'''


def write_symbol_lib() -> None:
    (ROOT / "CUTY.kicad_sym").write_text(
        f"(kicad_symbol_lib (version 20220914) (generator cuty_gen)\n{symbol()}\n)\n")


def write_footprint() -> None:
    lines = []
    sk = "(stroke (width 0.12) (type solid))"
    lines.append('(footprint "WeAct_BlackPill_Socket" (version 20221018) (generator cuty_gen) (layer "F.Cu")')
    lines.append('  (descr "WeAct Black Pill (STM32F401/F411) en dos zocalos hembra 1x20, 2.54 mm, filas a 15.24 mm. Pin 1 = PB12 junto al USB-C; pin 21 = VBAT junto al USB-C. Vista superior, componentes hacia arriba.")')
    lines.append('  (tags "STM32 BlackPill WeAct socket")')
    lines.append('  (attr through_hole)')
    lines.append(f'  (fp_text reference "REF**" (at {f(24.13)} {f(ROW_PITCH / 2 - 2)}) (layer "F.SilkS") (effects (font (size 1.2 1.2) (thickness 0.18))))')
    lines.append(f'  (fp_text value "WeAct_BlackPill_Socket" (at {f(24.13)} {f(ROW_PITCH / 2 + 2)}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))')
    # Module outline (fab) and USB-C marker.
    x0, x1 = 24.13 - MODULE_L / 2, 24.13 + MODULE_L / 2
    y0, y1 = ROW_PITCH / 2 - MODULE_W / 2, ROW_PITCH / 2 + MODULE_W / 2
    lines.append(f'  (fp_rect (start {f(x0)} {f(y0)}) (end {f(x1)} {f(y1)}) (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))')
    lines.append(f'  (fp_rect (start {f(x0 - 0.25)} {f(y0 - 0.25)}) (end {f(x1 + 0.25)} {f(y1 + 0.25)}) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))')
    usb_y0, usb_y1 = ROW_PITCH / 2 - 4.5, ROW_PITCH / 2 + 4.5
    lines.append(f'  (fp_rect (start {f(x0 + 0.4)} {f(usb_y0)}) (end {f(x0 + 6.3)} {f(usb_y1)}) {sk} (fill none) (layer "F.SilkS"))')
    lines.append(f'  (fp_text user "USB-C" (at {f(x0 + 2.6)} {f(ROW_PITCH / 2)} 90) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))')
    # Socket outlines on silkscreen.
    for y in (0.0, ROW_PITCH):
        lines.append(f'  (fp_rect (start -1.33 {f(y - 1.33)}) (end {f(48.26 + 1.33)} {f(y + 1.33)}) {sk} (fill none) (layer "F.SilkS"))')
    # Pin-1 marker.
    lines.append(f'  (fp_poly (pts (xy -1.9 -1.9) (xy -0.9 -1.9) (xy -1.9 -0.9)) {sk} (fill solid) (layer "F.SilkS"))')
    for i in range(20):
        x = i * PITCH
        for row, num, y, ty in ((0, i + 1, 0.0, 3.0), (1, i + 21, ROW_PITCH, ROW_PITCH + 3.0)):
            shape = "rect" if num == 1 else "circle"
            lines.append(f'  (pad "{num}" thru_hole {shape} (at {f(x)} {f(y)}) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask"))')
            name = BP_NAMES[str(num)].replace("3V3", "3V3")
            lines.append(f'  (fp_text user "{name}" (at {f(x)} {f(ty)} 90) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.13))))')
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
    print("library written")
