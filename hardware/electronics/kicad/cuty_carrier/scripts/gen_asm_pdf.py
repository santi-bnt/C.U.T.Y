"""Assembly drawing PDF for PCBWay (drawing + polarity notes + BOM), rendered with headless Chromium."""
import csv
import html
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PCBA = ROOT / "fab" / "pcba"
import base64
svg = '<img alt="assembly drawing" src="data:image/svg+xml;base64,' + base64.b64encode((PCBA / "cuty_carrier_ensamble.svg").read_bytes()).decode() + '">'
rows = list(csv.reader(open(PCBA / "cuty_carrier_PCBA_BOM.csv", encoding="utf-8")))
hdr, body = rows[0], rows[1:]
keep = [0, 1, 2, 3, 4, 5, 9]
bom = "".join("<tr>" + "".join(f"<td>{html.escape(r[i])}</td>" for i in keep) + "</tr>" for r in body)
doc = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size: A4 landscape; margin: 10mm; }}
body {{ font-family: 'DejaVu Sans', Arial, sans-serif; color: #111; margin: 0; }}
.pg {{ page-break-after: always; display: grid; grid-template-columns: 172mm 1fr; gap: 8mm; height: 186mm; overflow: hidden; }}
.pg:last-child {{ page-break-after: auto; display: block; height: auto; }}
h1 {{ font-size: 15pt; margin: 0 0 1mm; }} h2 {{ font-size: 10.5pt; margin: 4mm 0 1.5mm; }}
.sub {{ font-size: 8.5pt; color: #444; margin-bottom: 3mm; }}
.draw {{ border: .3mm solid #111; padding: 2mm; height: 158mm; display: flex; align-items: center; justify-content: center; }}
.draw img {{ width: 100%; height: 100%; object-fit: contain; }}
.side {{ font-size: 8.2pt; line-height: 1.38; }}
.side ul {{ padding-left: 4mm; margin: 0; }} .side li {{ margin-bottom: 1.2mm; }}
.k {{ display: inline-block; width: 3.2mm; height: 3.2mm; border-radius: 50%; border: .5mm solid #e5590f; vertical-align: -.6mm; }}
.box {{ border: .3mm solid #111; padding: 2mm 3mm; margin-top: 3mm; }}
table {{ border-collapse: collapse; width: 100%; font-size: 7.6pt; }}
th, td {{ border: .2mm solid #999; padding: 1mm 1.4mm; vertical-align: top; text-align: left; }}
th {{ background: #1f2937; color: #fff; }}
td:nth-child(1), td:nth-child(3) {{ text-align: center; width: 8mm; }}
</style></head><body>
<section class="pg">
  <div><h1>C.U.T.Y carrier v1.1 · Assembly drawing (top side)</h1>
  <div class="sub">PCB 100.1 × 92.1 mm, 2 layers, FR-4 1.6 mm · all parts through-hole, top side only · 39 placements, 225 THT joints · 0 SMD</div>
  <div class="draw">{svg}</div></div>
  <div class="side">
    <h2>Legend</h2>
    <ul>
      <li><span class="k"></span> Orange pad = pad 1: <b>+</b> on C1/C2, <b>K</b> (cathode) on D1–D4, <b>pin 1</b> on J12/J13/J14/U1, <b>negative</b> on J1.</li>
      <li>Grey pads: all other pins. Blue text: reference designators.</li>
    </ul>
    <h2>Polarity and orientation</h2>
    <ul>
      <li><b>C1, C2</b> 1000 µF: + lead in the square pad (pad 1). Body max 20 mm tall.</li>
      <li><b>D1</b> 1N5819: cathode band on the square pad side, as the silkscreen.</li>
      <li><b>D2/D3/D4</b> 3 mm LEDs (green/blue/red): cathode (flat side, short lead) in the square pad. Seat flush.</li>
      <li><b>J1</b> XT60PW-M (male): housing inside the silkscreen outline, mating face to the left board edge. Pad 1 = negative, pad 2 = battery +.</li>
      <li><b>J2–J6</b> Phoenix terminal blocks: wire entries face the nearest board edge.</li>
      <li><b>J12, J13</b> box headers: key slot toward the board edge marked on the silkscreen, pin 1 = square pad.</li>
      <li><b>U1</b>: two 1×20 female sockets only (Black Pill is plugged in later). Leave the 4 SWD holes empty.</li>
      <li><b>F1, F2</b>: fuse holders only, no fuses.</li>
      <li><b>JP1</b>: fit the jumper shunt after soldering.</li>
    </ul>
    <div class="box"><b>Assembly notes</b><br>
      Hand / selective solder is fine. All headers must stand perpendicular to the board (they mate with cables and a HAT).
      Clean flux residue. Substitutes with identical footprint and ratings are OK for resistors, C3, LEDs and pin headers;
      <b>do not substitute</b> J1, F1/F2 holders, J2–J6 terminal blocks or C1/C2 (height limit).</div>
  </div>
</section>
<section class="pg">
  <h1>Bill of materials · turnkey</h1>
  <div class="sub">Files: cuty_carrier_PCBA_BOM.xlsx (BOM) · cuty_carrier_PCBA_CPL.xlsx (centroid, mm, origin = lower-left board corner, Y up)</div>
  <table><tr>{''.join(f'<th>{html.escape(hdr[i])}</th>' for i in keep)}</tr>{bom}</table>
  <h2>Not assembled (supplied and fitted by the owner)</h2>
  <div class="side">WeAct Black Pill STM32F401CCU6 module · mini blade fuses 10 A (F1) and 5 A (F2) · 4 × M3 standoffs (H1–H4)</div>
</section>
</body></html>"""
out_html = PCBA / "_asm.html"
out_html.write_text(doc, encoding="utf-8")
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto(out_html.as_uri())
    pg.pdf(path=str(PCBA / "cuty_carrier_PCBA_ensamble.pdf"), format="A4", landscape=True, print_background=True,
           margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"})
    b.close()
out_html.unlink()
print("pdf ok")
