"""Read-only export of the real carrier layout/netlist into the static website.

No KiCad installation needed; parses native S-expressions and checks every named
pad against the project's netlist before writing web-only assets.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import runpy
import shutil
import zipfile

WEB = Path(__file__).resolve().parents[1]
ROOT = WEB.parent
SOURCE = ROOT / "hardware/electronics/kicad/cuty_carrier"
OUT = WEB / "public/engineering"


def parse(text):
    stack = [[]]
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text):
        if token == "(":
            child = []
            stack[-1].append(child)
            stack.append(child)
        elif token == ")":
            stack.pop()
        else:
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    assert len(stack) == 1
    return stack[0][0]


def entries(node, name):
    return [x for x in node if isinstance(x, list) and x and x[0] == name]


def item(node, name):
    return next(iter(entries(node, name)), None)


def main():
    source_bytes = (SOURCE / "cuty_carrier.kicad_pcb").read_bytes()
    board = parse(source_bytes.decode())
    netlist = runpy.run_path(str(SOURCE / "scripts/netlist.py"))
    parts = netlist["build"]()
    netlist["check"](parts)
    by_ref = {p.ref: p for p in parts}
    result = []
    for fp in entries(board, "footprint"):
        reference = next(x[2] for x in entries(fp, "fp_text") if x[1] == "reference")
        part = by_ref[reference]
        at = item(fp, "at")
        ox, oy = float(at[1]), float(at[2])
        theta = math.radians(float(at[3]) if len(at) > 3 else 0)
        pins = []
        xs, ys = [], []
        for pad in entries(fp, "pad"):
            pos, size = item(pad, "at"), item(pad, "size")
            px, py = float(pos[1]), float(pos[2])
            x = ox + px * math.cos(theta) + py * math.sin(theta) - 100
            y = oy - px * math.sin(theta) + py * math.cos(theta) - 50
            radius = max(float(size[1]), float(size[2])) / 2
            xs.extend((x - radius, x + radius))
            ys.extend((y - radius, y + radius))
            net = item(pad, "net")
            net_name = net[2] if net else ""
            if pad[1]:
                assert part.pins[pad[1]] == net_name, (reference, pad[1], net_name)
                pins.append({"pin": pad[1], "net": net_name, "x": round(x, 3), "y": round(y, 3),
                             "label": netlist["BP_NAMES"].get(pad[1], "") if reference == "U1" else ""})
        bounds = [min(xs) - 1, min(ys) - 1, max(xs) - min(xs) + 2, max(ys) - min(ys) + 2]
        result.append({"ref": reference, "value": part.value, "note": part.note, "group": part.group,
                       "mpn": part.mpn, "footprint": fp[1], "bounds": [round(x, 3) for x in bounds],
                       "pins": sorted(pins, key=lambda p: int(p["pin"]))})
    assert len(result) == len(parts)
    manifest = {"revision": "1.1", "sizeMm": [100, 92], "thicknessMm": 1.6, "layers": 2,
                "pcbModel": None, "source": "hardware/electronics/kicad/cuty_carrier",
                "pcbSha256": hashlib.sha256(source_bytes).hexdigest(),
                "netlistSha256": hashlib.sha256((SOURCE / "scripts/netlist.py").read_bytes()).hexdigest(),
                "piHeader": netlist["PI_HEADER"], "displayUsed": netlist["DISPLAY_USED"],
                "respeakerUsed": netlist["RESPEAKER_USED"],
                "respeakerMustBeOpen": netlist["RESPEAKER_MUST_BE_OPEN"],
                "components": sorted(result, key=lambda p: (re.sub(r'\d', '', p['ref']), int(re.sub(r'\D', '', p['ref']))))}
    (WEB / "src/data/carrier.generated.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    for src, dest in [
        ("cuty_carrier.kicad_pcb", "carrier.kicad_pcb"),
        ("cuty_carrier.kicad_sch", "carrier.kicad_sch"),
        ("fab/cuty_carrier_BOM.csv", "carrier-bom.csv"),
        ("fab/cuty_carrier_esquematico.pdf", "carrier-schematic.pdf"),
        ("fab/cuty_carrier_capa_superior.pdf", "carrier-top.pdf"),
        ("fab/preview/cuty_carrier_top.png", "carrier-front.png"),
        ("fab/preview/cuty_carrier_bottom.png", "carrier-back.png"),
        ("fab/jlcpcb/BOM_JLCPCB.csv", "jlcpcb-bom.csv"),
        ("fab/jlcpcb/CPL_JLCPCB.csv", "jlcpcb-cpl.csv"),
        ("fab/jlcpcb/LEEME_JLCPCB.md", "jlcpcb-order-notes.md"),
        ("fab/pcba/cuty_carrier_PCBA_BOM.xlsx", "pcba-bom.xlsx"),
        ("fab/pcba/cuty_carrier_PCBA_CPL.xlsx", "pcba-cpl.xlsx"),
        ("fab/pcba/cuty_carrier_PCBA_ensamble.pdf", "pcba-assembly.pdf"),
        ("fab/pcba/LEEME_PCBA.md", "pcba-readme.md"),
        ("README.md", "carrier-readme.md"),
    ]:
        shutil.copyfile(SOURCE / src, OUT / dest)
    shutil.copyfile(ROOT / "docs/bom.md", OUT / "project-bom.md")
    with zipfile.ZipFile(OUT / "carrier-gerbers.zip", "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted((SOURCE / "fab/gerbers").iterdir()):
            if path.is_file():
                info = zipfile.ZipInfo(path.name, (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                bundle.writestr(info, path.read_bytes())
    project_files = ["cuty_carrier.kicad_pcb", "cuty_carrier.kicad_sch", "cuty_carrier.kicad_pro", "CUTY.kicad_sym", "fp-lib-table", "sym-lib-table", "README.md", "CUTY.pretty/WeAct_BlackPill_Socket.kicad_mod"]
    with zipfile.ZipFile(OUT / "carrier-project.zip", "w", zipfile.ZIP_DEFLATED) as bundle:
        for name in project_files:
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, (SOURCE / name).read_bytes())
    print(f"Exported {len(result)} actual footprints; pad/net parity passed. No verified PCB 3D export present.")


if __name__ == "__main__":
    main()
