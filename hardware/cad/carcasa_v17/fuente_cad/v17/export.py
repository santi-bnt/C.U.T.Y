"""Export the C.U.T.Y V17 package: per-part STEP (assembly position), print-oriented STL,
a coloured multi-component assembly STEP (opens in Fusion as components) and the web GLB."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import cadquery as cq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import V   # noqa
import build

PKG = build.OUT / "CUTY_V17_Nido"

# print orientation: list of (axis, degrees) rotations applied about the part's own centre
ORIENT = {
    "G2_Crank_L": [((1, 0, 0), 90)], "G3_Crank_R": [((1, 0, 0), 90)],
    "K1_Core_Deck": [((1, 0, 0), 180)], "K2_Core_Spine": [((1, 0, 0), -90)],
    "K3_Core_Shoulders": [((1, 0, 0), 180)], "K5_Power_Rack": [((1, 0, 0), -90)],
    "S1_Body_Front": [((1, 0, 0), -90)], "S2_Body_Back": [((1, 0, 0), 90)],
    "S3_Tummy_Grille": [((1, 0, 0), -90)], "S4_USB_Plug": [((0, 1, 0), 90)],
    "A1_Arm_L": [((0, 1, 0), -90)], "A2_Arm_R": [((0, 1, 0), 90)],
    "A3_Hand_L": [((0, 1, 0), -90)], "A4_Hand_R": [((0, 1, 0), 90)],
    "A5_Arm_Cap_L": [((0, 1, 0), -90)], "A6_Arm_Cap_R": [((0, 1, 0), 90)],
    "H1_Head_Front": [((1, 0, 0), -90)], "H2_Head_Back": [((1, 0, 0), 90)],
    "H3_Visor": [((1, 0, 0), 90)], "H4_Display_Bars": [((1, 0, 0), 90)],
    "H6_Ear_L": [((0, 1, 0), -90)], "H7_Ear_R": [((0, 1, 0), 90)],
}


def oriented(name, shape):
    s = shape
    c = s.Center()
    for ax, deg in ORIENT.get(name, []):
        s = s.rotate(c, c + V(*ax), deg)
    b = s.BoundingBox()
    return s.translate(V(-(b.xmin + b.xmax) / 2, -(b.ymin + b.ymax) / 2, -b.zmin))


def _watertight(path):
    """Close the odd sliver OCC leaves at sphere poles so every slicer sees a closed mesh."""
    import trimesh
    m = trimesh.load(str(path))
    if not m.is_watertight:
        m.update_faces(m.nondegenerate_faces(height=1e-6))
        m.update_faces(m.unique_faces())
        m.remove_unreferenced_vertices()
        m.merge_vertices(digits_vertex=3)
        trimesh.repair.fill_holes(m)
        trimesh.repair.fix_normals(m)
        m.export(str(path))
    if not m.is_watertight:
        print("WARNING not watertight:", path.name)


def main():
    if PKG.exists():
        shutil.rmtree(PKG)
    for d in ("STEP_partes", "STL_imprimir", "STEP_ensamble"):
        (PKG / d).mkdir(parents=True)
    printed, bought = [], []
    assy = cq.Assembly(name="CUTY_V17_Nido")
    for name, fn, col, grp, _ in build.PRINTED:
        s = build.cached(name, fn)
        cq.exporters.export(s, str(PKG / "STEP_partes" / f"{name}.step"))
        o = oriented(name, s)
        stl = PKG / "STL_imprimir" / f"{name}.stl"
        cq.exporters.export(o, str(stl), tolerance=0.02, angularTolerance=0.1)
        _watertight(stl)
        assy.add(s, name=name, color=cq.Color(*col))
        b = o.BoundingBox()
        printed.append(dict(part=name, group=grp, print_dims_mm=[round(b.xlen, 1), round(b.ylen, 1), round(b.zlen, 1)],
                            volume_cm3=round(s.Volume() / 1000, 1)))
        print("exported", name, flush=True)
    refs_assy = cq.Assembly(name="Componentes_comprados")
    for n, s, c, g in build.purchased():
        refs_assy.add(s, name=n, color=cq.Color(*c))
        bought.append(n)
    assy.add(refs_assy, name="Componentes_comprados")
    assy.save(str(PKG / "STEP_ensamble" / "CUTY_V17_Ensamble_completo.step"))
    (PKG / "partes.json").write_text(json.dumps(dict(printed=printed, purchased_refs=bought), indent=1))
    print("assembly saved")


if __name__ == "__main__":
    main()
