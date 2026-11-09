"""PCBWay turnkey assembly files: BOM (xlsx + csv) and pick-and-place / centroid (xlsx + csv).

Run with KiCad's Python:  /usr/bin/python3 gen_pcba.py
Every through-hole part is assembled by PCBWay except the plug-in modules (Black Pill, fuses),
which the owner inserts by hand.
"""
import csv
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "fab" / "pcba"

# designators -> (qty per designator, manufacturer, MPN, description, supplier link, assembly note)
LINES = [
    (["C1", "C2"], 1, "Nichicon", "UHE1C102MPD", "Aluminum electrolytic 1000 uF 16 V, low ESR, D10 x 20 mm, 5.0 mm pitch",
     "https://www.digikey.com/en/products/detail/nichicon/UHE1C102MPD/589267",
     "Polarized: + lead in the square pad (pad 1). Max body height 20 mm."),
    (["C3"], 1, "Vishay", "K104K15X7RF5TL2", "Ceramic capacitor 100 nF 50 V X7R, radial 5.0 mm pitch", "", ""),
    (["D1"], 1, "onsemi", "1N5819RLG", "Schottky diode 40 V 1 A, DO-41", "",
     "Cathode band to the square pad (pad 1), as the silkscreen."),
    (["D2"], 1, "Kingbright", "WP710A10SGD", "LED 3 mm green", "",
     "Cathode (flat side, short lead) in the square pad (pad 1). Flush with the board."),
    (["D3"], 1, "Kingbright", "WP710A10QBC/D", "LED 3 mm blue", "https://www.digikey.com/en/products/detail/kingbright/WP710A10QBC-D/2769812",
     "Cathode (flat side, short lead) in the square pad (pad 1). Flush with the board."),
    (["D4"], 1, "Kingbright", "WP710A10ID", "LED 3 mm red", "",
     "Cathode (flat side, short lead) in the square pad (pad 1). Flush with the board."),
    (["F1", "F2"], 1, "Keystone Electronics", "3568", "Fuse holder, mini blade (ATM), PCB mount, 4 pins", "",
     "Holder only. Do NOT insert fuses (owner inserts 10 A in F1 and 5 A in F2)."),
    (["J1"], 1, "Changzhou Amass", "XT60PW-M", "XT60 male, right angle, PCB mount (LCSC C98732)",
     "https://lcsc.com/product-detail/Power-Connectors_Changzhou-Amass-Elec-XT60PW-M_C98732.html",
     "Male. Housing exactly inside the silkscreen outline: pad 1 (square) = negative, pad 2 = positive (battery +). Do not substitute."),
    (["J2", "J3", "J4", "J5", "J6"], 1, "Phoenix Contact", "1715721", "Terminal block MKDS 1,5/2-5,08, 2 pos, 5.08 mm",
     "", "Wire entries face the nearest board edge, as the silkscreen outline. Do not substitute pitch."),
    (["J7", "J8", "J9", "J10", "J11"], 1, "Sullins", "PREC003SAAN-RC", "Pin header male 1x3, 2.54 mm, vertical", "",
     "Can be cut from a breakaway strip."),
    (["J15"], 1, "Sullins", "PREC004SAAN-RC", "Pin header male 1x4, 2.54 mm, vertical", "", "Can be cut from a breakaway strip."),
    (["JP1"], 1, "Sullins", "PREC002SAAN-RC", "Pin header male 1x2, 2.54 mm, vertical", "", "Can be cut from a breakaway strip."),
    (["JP1 (shunt)"], 1, "Sullins", "SPC02SYAN", "Jumper shunt 2.54 mm", "", "Fit the shunt on JP1 after soldering."),
    (["J12"], 1, "Wurth Elektronik", "61204021621", "Box header (shrouded) 2x20, 2.54 mm, vertical", "",
     "Keyed: key slot and pin 1 (square pad) exactly as the silkscreen."),
    (["J13"], 1, "Wurth Elektronik", "61202621621", "Box header (shrouded) 2x13, 2.54 mm, vertical", "",
     "Keyed: key slot and pin 1 (square pad) exactly as the silkscreen."),
    (["J14"], 1, "Sullins", "PRPC020DAAN-RC", "Pin header male 2x20, 2.54 mm, vertical", "", ""),
    (["U1"], 2, "Sullins", "PPTC201LFBN-RC", "Female socket 1x20, 2.54 mm, 8.5 mm tall",
     "", "Two 1x20 female sockets in the two 20-pin rows. Leave the 4 SWD holes (marked SWD) empty. Do not install any module."),
    (["R1", "R2", "R3", "R4", "R5"], 1, "Yageo", "MFR-25FBF52-220R", "Resistor 220 ohm 1% 1/4 W metal film, axial", "", ""),
    (["R6"], 1, "Yageo", "MFR-25FBF52-100K", "Resistor 100 kohm 1% 1/4 W metal film, axial", "", ""),
    (["R7"], 1, "Yageo", "MFR-25FBF52-22K", "Resistor 22 kohm 1% 1/4 W metal film, axial", "", ""),
    (["R8", "R9"], 1, "Yageo", "MFR-25FBF52-1K", "Resistor 1 kohm 1% 1/4 W metal film, axial", "", ""),
    (["R10", "R11", "R12"], 1, "Yageo", "MFR-25FBF52-4K7", "Resistor 4.7 kohm 1% 1/4 W metal film, axial", "", ""),
]
NOT_ASSEMBLED = [
    ("U1 module", 1, "WeAct Studio", "Black Pill STM32F401CCU6", "Plugged in by the owner"),
    ("F1 fuse", 1, "Littelfuse", "0297010.WXNV", "Mini blade 10 A, inserted by the owner"),
    ("F2 fuse", 1, "Littelfuse", "0297005.WXNV", "Mini blade 5 A, inserted by the owner"),
    ("H1-H4", 4, "-", "M3 x 10 standoff + screw", "Mounting to the robot spine"),
]


def main():
    b = pcbnew.LoadBoard(str(ROOT / "cuty_carrier.kicad_pcb"))
    bb = b.GetBoardEdgesBoundingBox()
    x0, y1 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetBottom())
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    # ---- sanity: every placed part is on exactly one BOM line, values agree with the board
    on_bom = [r for refs, *_ in LINES for r in refs if r in fps]
    placed = [r for r, f in fps.items() if not (f.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM)]
    missing = sorted(set(placed) - set(on_bom))
    dup = sorted({r for r in on_bom if on_bom.count(r) > 1})
    if missing or dup:
        sys.exit(f"BOM mismatch: missing {missing}, duplicated {dup}")
    OUT.mkdir(parents=True, exist_ok=True)
    # ---- BOM
    hdr = ["Item #", "Designator", "Qty", "Manufacturer", "Mfg Part #", "Description / Value", "Package / Footprint",
           "Type", "Supplier link", "Your Instructions / Notes"]
    rows = []
    for i, (refs, per, mfr, mpn, desc, link, note) in enumerate(LINES, 1):
        real = [r for r in refs if r in fps]
        fp = str(fps[real[0]].GetFPID().GetLibItemName()) if real else "-"
        qty = len(refs) * per
        rows.append([i, ",".join(refs), qty, mfr, mpn, desc, fp, "THT", link, note])
    write(OUT / "cuty_carrier_PCBA_BOM", hdr, rows, "BOM",
          extra=[["", "No ensamblar (los pone el dueño):"]] + [["", d, q, m, p, n] for d, q, m, p, n in NOT_ASSEMBLED])
    # ---- centroid / pick and place (body centre = pad bounding box centre, Y up from the lower-left corner)
    hdr2 = ["Designator", "Mid X (mm)", "Mid Y (mm)", "Layer", "Rotation", "Ref X (mm)", "Ref Y (mm)", "Value", "Footprint"]
    rows2 = []
    for ref in sorted(on_bom, key=lambda r: (r[0], int("".join(c for c in r if c.isdigit()) or 0))):
        f = fps[ref]
        xs, ys = [], []
        for p in f.Pads():
            if p.GetNumber() == "":
                continue
            bbp = p.GetBoundingBox()
            xs += [bbp.GetLeft(), bbp.GetRight()]
            ys += [bbp.GetTop(), bbp.GetBottom()]
        cx, cy = pcbnew.ToMM((min(xs) + max(xs)) / 2), pcbnew.ToMM((min(ys) + max(ys)) / 2)
        pos = f.GetPosition()
        rows2.append([ref, round(cx - x0, 3), round(y1 - cy, 3), "Top",
                      round(f.GetOrientationDegrees() % 360, 1), round(pcbnew.ToMM(pos.x) - x0, 3),
                      round(y1 - pcbnew.ToMM(pos.y), 3), f.GetValue(), str(f.GetFPID().GetLibItemName())])
    write(OUT / "cuty_carrier_PCBA_CPL", hdr2, rows2, "CPL")
    pins = sum(len([p for p in fps[r].Pads() if p.GetNumber() != ""]) for r in on_bom)
    uniq = len(LINES)
    print(f"BOM lines {len(LINES)}, placements {sum(len(r[1].split(',')) for r in rows)}, "
          f"THT pins {pins}, CPL rows {len(rows2)}, board {pcbnew.ToMM(bb.GetWidth())} x {pcbnew.ToMM(bb.GetHeight())} mm")


def write(stem, hdr, rows, sheet, extra=()):
    with open(stem.with_suffix(".csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(hdr)
        w.writerows(rows)
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        return
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet
    ws.append(hdr)
    for r in rows:
        ws.append(r)
    for r in extra:
        ws.append(r)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F2937")
        c.alignment = Alignment(vertical="center", wrap_text=True)
    widths = {"A": 8, "B": 22, "C": 8, "D": 20, "E": 22, "F": 48, "G": 40, "H": 7, "I": 40, "J": 60}
    if sheet == "CPL":
        widths = {"A": 12, "B": 12, "C": 12, "D": 8, "E": 10, "F": 12, "G": 12, "H": 18, "I": 52}
    for k, v in widths.items():
        ws.column_dimensions[k].width = v
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(vertical="top", wrap_text=True)
    ws.freeze_panes = "A2"
    wb.save(stem.with_suffix(".xlsx"))


if __name__ == "__main__":
    main()
