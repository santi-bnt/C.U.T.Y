"""Independent check of the files PCBWay will actually receive (fab/gerbers).

Rasterizes the copper Gerbers, joins the two layers through every plated hole
in the Excellon file, labels connected copper and compares it with the design
nets read from the .kicad_pcb:
  * no open: all pads of a net sit on one piece of copper;
  * no short: one piece of copper never carries two nets, except GND+PGND,
    and those two separate once the NT1 net-tie bridge is cut (single point);
  * every pad has a drill of the right size and a solder-mask opening.

    /usr/bin/python3 verify_gerbers.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import pcbnew
from PIL import Image
from scipy import ndimage

from gerbonara import ExcellonFile, GerberFile

ROOT = Path(__file__).resolve().parents[1]
G = ROOT / "fab" / "gerbers"
S = 40                      # pixels per mm (0.025 mm); smallest gap is 0.25 mm = 10 px
Image.MAX_IMAGE_PIXELS = None


def raster(path: Path, bounds) -> np.ndarray:
    (x0, y0), (x1, y1) = bounds
    svg = GerberFile.open(path).to_svg(force_bounds=bounds, fg="black", bg="white")
    with tempfile.TemporaryDirectory() as tmp:
        sp, pp = Path(tmp) / "l.svg", Path(tmp) / "l.png"
        sp.write_text(str(svg))
        subprocess.run(["rsvg-convert", "-b", "white", "-w", str(round((x1 - x0) * S)),
                        "-h", str(round((y1 - y0) * S)), str(sp), "-o", str(pp)], check=True)
        return np.asarray(Image.open(pp).convert("L")) < 128


def main() -> int:
    edge = GerberFile.open(next(G.glob("*Edge_Cuts*")))
    (ex0, ey0), (ex1, ey1) = edge.bounding_box()
    print(f"outline from Gerber: {ex1 - ex0:.2f} x {ey1 - ey0:.2f} mm")
    bounds = ((ex0 - 1, ey0 - 1), (ex1 + 1, ey1 + 1))
    (bx0, by0), (bx1, by1) = bounds

    def px(x, y):                       # Gerber mm (y up) -> pixel (col, row)
        return int(round((x - bx0) * S)), int(round((by1 - y) * S))

    cu = {side: raster(next(G.glob(f"*{side}_Cu*")), bounds) for side in ("F", "B")}
    mask = {side: raster(next(G.glob(f"*{side}_Mask*")), bounds) for side in ("F", "B")}
    pth = ExcellonFile.open(next(G.glob("*-PTH.drl")))
    npth = ExcellonFile.open(next(G.glob("*-NPTH.drl")))

    def holes(exc):
        out = []
        for obj in exc.objects:
            d = obj.tool.diameter
            if hasattr(obj, "x1"):          # slot
                out.append(((obj.x1 + obj.x2) / 2, (obj.y1 + obj.y2) / 2, d, True))
            else:
                out.append((obj.x, obj.y, d, False))
        return out

    plated, unplated = holes(pth), holes(npth)
    print(f"drills: {len(plated)} plated ({sum(h[3] for h in plated)} slots), {len(unplated)} non-plated")

    # Design pads (KiCad page coords: y down -> Gerber y = -y).
    board = pcbnew.LoadBoard(str(ROOT / "cuty_carrier.kicad_pcb"))
    pads = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            pos = p.GetPosition()
            pads.append(dict(ref=fp.GetReference(), num=p.GetNumber(), net=p.GetNetname(),
                             x=pcbnew.ToMM(pos.x), y=-pcbnew.ToMM(pos.y),
                             drill=pcbnew.ToMM(min(p.GetDrillSize().x, p.GetDrillSize().y)),
                             pth=p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH))

    def label(cut=None):
        layers = {}
        for side, img in cu.items():
            img = img.copy()
            if cut is not None:
                c0, r0, c1, r1 = cut
                img[r0:r1, c0:c1] = False
            lab, n = ndimage.label(img)
            layers[side] = (lab, n)
        off = layers["F"][1] + 1
        parent = list(range(off + layers["B"][1] + 1))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        def comp(side, x, y):
            lab = layers[side][0]
            c, r = px(x, y)
            v = lab[r, c]
            return 0 if v == 0 else v + (off if side == "B" else 0)

        for x, y, d, _ in plated:          # plating joins both layers
            a, b = comp("F", x, y), comp("B", x, y)
            if a and b:
                parent[find(a)] = find(b)
        return lambda x, y: find(comp("F", x, y) or comp("B", x, y))

    errors = []
    root = label()
    net_roots, root_nets = defaultdict(set), defaultdict(set)
    for p in pads:
        if not p["pth"]:
            continue
        r = root(p["x"], p["y"])
        if r == 0:
            errors.append(f"{p['ref']}.{p['num']}: no copper at pad")
            continue
        key = p["net"] or f"<sin red {p['ref']}.{p['num']}>"
        net_roots[key].add(r)
        root_nets[r].add(key)
    opens = {n: len(r) for n, r in net_roots.items() if len(r) > 1 and not n.startswith("<")}
    shorts = [sorted(n) for n in root_nets.values() if len(n) > 1 and set(n) != {"GND", "PGND"}]
    errors += [f"OPEN {n}: {k} pieces" for n, k in opens.items()]
    errors += [f"SHORT {' + '.join(n)}" for n in shorts]
    real_nets = [n for n in net_roots if not n.startswith("<")]
    print(f"copper pieces: {len(root_nets)} carrying {len(real_nets)} nets; opens {len(opens)}, shorts {len(shorts)}")

    # Single-point ground: cut the NT1 bridge and GND/PGND must come apart.
    nt = {p["num"]: p for p in pads if p["ref"] == "NT1"}
    xa, xb = sorted((nt["1"]["x"], nt["2"]["x"]))
    c0, r0 = px(xa + 0.70, nt["1"]["y"] + 1.0)
    c1, r1 = px(xb - 0.70, nt["1"]["y"] - 1.0)
    cut_root = label((c0, r0, c1, r1))
    g = {cut_root(p["x"], p["y"]) for p in pads if p["net"] == "GND" and p["pth"]}
    pg = {cut_root(p["x"], p["y"]) for p in pads if p["net"] == "PGND" and p["pth"]}
    if g & pg:
        errors.append("GND and PGND still joined with NT1 cut: a second ground link exists")
    print(f"NT1 cut -> GND pieces {len(g)}, PGND pieces {len(pg)}, shared {len(g & pg)}")

    # Drill and mask for every pad.
    for p in pads:
        if not p["drill"]:
            continue
        pool = plated if p["pth"] else unplated
        hit = [h for h in pool if abs(h[0] - p["x"]) < 0.05 and abs(h[1] - p["y"]) < 0.05]
        if not hit:
            errors.append(f"{p['ref']}.{p['num']}: no drill")
        elif abs(hit[0][2] - p["drill"]) > 0.02:
            errors.append(f"{p['ref']}.{p['num']}: drill {hit[0][2]} != {p['drill']}")
        if p["pth"] and p["ref"] != "NT1":     # the net tie is bare copper, never soldered
            for side in ("F", "B"):
                c, r = px(p["x"], p["y"])
                if not mask[side][r, c]:
                    errors.append(f"{p['ref']}.{p['num']}: covered by {side} solder mask")
    vias = sum(1 for t in board.GetTracks() if t.GetClass() == "PCB_VIA")
    pad_holes = sum(1 for p in pads if p["drill"])
    if len(plated) + len(unplated) != pad_holes + vias:
        errors.append(f"drill count {len(plated) + len(unplated)} != pads {pad_holes} + vias {vias}")
    print("errors:", errors or "none")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
