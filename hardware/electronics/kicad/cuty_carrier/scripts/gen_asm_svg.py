"""Clean assembly drawing (SVG) straight from the board: outline, pads, fab outlines, designators and
polarity callouts. Used for the PCBWay assembly PDF and the build guide."""
import math
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
POLAR = {"C1": "+", "C2": "+", "D1": "K", "D2": "K", "D3": "K", "D4": "K", "J12": "1", "J13": "1", "J14": "1",
         "U1": "1", "J1": "−"}
M = 2.0  # margin mm


def mm(v):
    return pcbnew.ToMM(v)


def main(out):
    b = pcbnew.LoadBoard(str(ROOT / "cuty_carrier.kicad_pcb"))
    bb = b.GetBoardEdgesBoundingBox()
    X0, Y0 = mm(bb.GetLeft()) - M, mm(bb.GetTop()) - M
    W, H = mm(bb.GetWidth()) + 2 * M, mm(bb.GetHeight()) + 2 * M
    P = lambda v: (round(mm(v.x) - X0, 3), round(mm(v.y) - Y0, 3))
    el = []

    def shape_svg(s, cls):
        st = s.GetShape()
        if st == pcbnew.SHAPE_T_SEGMENT:
            (x1, y1), (x2, y2) = P(s.GetStart()), P(s.GetEnd())
            return f'<line class="{cls}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>'
        if st == pcbnew.SHAPE_T_RECT:
            (x1, y1), (x2, y2) = P(s.GetStart()), P(s.GetEnd())
            return f'<rect class="{cls}" x="{min(x1, x2)}" y="{min(y1, y2)}" width="{abs(x2 - x1)}" height="{abs(y2 - y1)}"/>'
        if st == pcbnew.SHAPE_T_CIRCLE:
            (cx, cy) = P(s.GetCenter())
            return f'<circle class="{cls}" cx="{cx}" cy="{cy}" r="{round(mm(s.GetRadius()), 3)}"/>'
        if st == pcbnew.SHAPE_T_ARC:
            (x1, y1), (x2, y2) = P(s.GetStart()), P(s.GetEnd())
            r = round(mm(s.GetRadius()), 3)
            ang = s.GetArcAngle().AsDegrees()
            large = 1 if abs(ang) > 180 else 0
            sweep = 1 if ang > 0 else 0
            return f'<path class="{cls}" d="M{x1} {y1} A{r} {r} 0 {large} {sweep} {x2} {y2}"/>'
        if st == pcbnew.SHAPE_T_POLY:
            pts = s.GetPolyShape().Outline(0)
            d = " ".join(f"{round(mm(pts.CPoint(i).x) - X0, 3)},{round(mm(pts.CPoint(i).y) - Y0, 3)}" for i in range(pts.PointCount()))
            return f'<polygon class="{cls}" points="{d}"/>'
        return ""

    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and isinstance(d, pcbnew.PCB_SHAPE):
            el.append(shape_svg(d, "edge"))
    marks = []
    for f in b.GetFootprints():
        ref = f.GetReference()
        for g in f.GraphicalItems():
            if isinstance(g, pcbnew.PCB_SHAPE) and g.GetLayer() == pcbnew.F_Fab:
                el.append(shape_svg(g, "fab"))
        for p in f.Pads():
            if p.GetNumber() == "" and p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            cx, cy = P(p.GetPosition())
            sz = p.GetSize()
            w, h = mm(sz.x), mm(sz.y)
            rot = -p.GetOrientationDegrees()
            first = p.GetNumber() == "1"
            cls = "pad1" if (first and ref in POLAR) else "pad"
            if p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE:
                el.append(f'<circle class="{cls}" cx="{cx}" cy="{cy}" r="{round(w / 2, 3)}"/>')
            else:
                rr = min(w, h) / 2 if p.GetShape() == pcbnew.PAD_SHAPE_OVAL else 0
                el.append(f'<rect class="{cls}" x="{round(cx - w / 2, 3)}" y="{round(cy - h / 2, 3)}" width="{round(w, 3)}" '
                          f'height="{round(h, 3)}" rx="{round(rr, 3)}" transform="rotate({rot} {cx} {cy})"/>')
            dr = mm(p.GetDrillSize().x)
            if dr > 0:
                el.append(f'<circle class="hole" cx="{cx}" cy="{cy}" r="{round(dr / 2, 3)}"/>')
            if first and ref in POLAR:
                marks.append((ref, cx, cy, POLAR[ref]))
        if ref.startswith(("H", "NT")):
            continue
        # designator at the footprint's fab reference text if any, else at the centre
        xs, ys = [], []
        for g in f.GraphicalItems():
            if isinstance(g, pcbnew.PCB_SHAPE) and g.GetLayer() == pcbnew.F_Fab:
                gb = g.GetBoundingBox()
                xs += [gb.GetLeft(), gb.GetRight()]
                ys += [gb.GetTop(), gb.GetBottom()]
        if not xs:
            for q in f.Pads():
                qb = q.GetBoundingBox()
                xs += [qb.GetLeft(), qb.GetRight()]
                ys += [qb.GetTop(), qb.GetBottom()]
        pos = (round(mm((min(xs) + max(xs)) / 2) - X0, 3), round(mm((min(ys) + max(ys)) / 2) - Y0, 3))
        if ref.startswith("D") and ref != "D1":
            pos = (pos[0], round(pos[1] + 2.9, 3))            # LEDs: label under the body
        el.append(f'<text class="ref" x="{pos[0]}" y="{pos[1]}">{ref}</text>')
    for ref, cx, cy, sym in marks:
        el.append(f'<g class="mk"><circle cx="{cx}" cy="{cy}" r="1.55"/><text x="{cx}" y="{cy}">{sym}</text></g>')
    css = """
.edge{fill:none;stroke:#111;stroke-width:.35}
.fab{fill:none;stroke:#333;stroke-width:.14}
.pad{fill:#c9cdd3;stroke:none}
.pad1{fill:#e5590f;stroke:none}
.hole{fill:#fff}
.ref{font:700 1.6px 'DejaVu Sans',Arial,sans-serif;fill:#0b5cad;text-anchor:middle;dominant-baseline:central;paint-order:stroke;stroke:#fff;stroke-width:.55px}
.mk circle{fill:none;stroke:#e5590f;stroke-width:.3}
.mk text{font:700 1.15px 'DejaVu Sans',Arial,sans-serif;fill:#fff;text-anchor:middle;dominant-baseline:central}
"""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.3f} {H:.3f}" width="{W:.3f}mm" height="{H:.3f}mm">'
           f'<style>{css}</style><rect x="0" y="0" width="{W:.3f}" height="{H:.3f}" fill="#fff"/>' + "".join(el) + "</svg>")
    Path(out).write_text(svg)
    print("svg", out, round(W, 2), round(H, 2), len(marks), "polarity marks")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "fab" / "pcba" / "cuty_carrier_ensamble.svg"))
