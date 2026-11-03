"""BOM grouped by value/footprint, for buying parts (THT, hand soldered)."""
import csv
from collections import OrderedDict
from pathlib import Path
from netlist import build

ROOT = Path(__file__).resolve().parents[1]
groups: "OrderedDict[tuple, list]" = OrderedDict()
for p in build():
    if p.group == "mech" or p.symbol == "Device:NetTie_2":
        continue
    groups.setdefault((p.value, p.footprint[1], p.mpn, p.note if p.ref.startswith(("J", "U", "F")) else ""), []).append(p.ref)
rows = [("Referencias", "Cantidad", "Valor", "Footprint", "Comprar", "Nota")]
for (value, fp, mpn, note), refs in groups.items():
    rows.append((" ".join(refs), len(refs), value, fp, mpn, note))
extra = [
    ("-", 2, "Fusible mini blade", "-", "Fusible automotriz mini 10 A + 5 A", "Para F1 (servos) y F2 (Pi)"),
    ("-", 1, "Cable plano 40 vias", "-", "Cable IDC 2x20 hembra-hembra 10-15 cm", "J12 a la Raspberry Pi 5"),
    ("-", 1, "Cable pantalla 26 vias", "-", "Extension GPIO 26 vias hembra-macho (o IDC 2x13 H-H + tira 2x13 macho-macho)", "J13 a la pantalla Display-G"),
    ("-", 1, "Jumper", "-", "Jumper 2.54 mm", "JP1"),
    ("-", 4, "Tornillo M3", "-", "Separador M3 10 mm + tornillo", "H1-H4"),
]
rows += extra
with open(ROOT / "fab" / "cuty_carrier_BOM.csv", "w", newline="", encoding="utf-8") as fh:
    csv.writer(fh).writerows(rows)
for r in rows:
    print(" | ".join(str(c) for c in r))
