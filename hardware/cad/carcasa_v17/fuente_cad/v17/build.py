"""Build every part of C.U.T.Y V17, verify it and export STEP / STL / GLB.

python3 build.py [--fast]   (--fast skips the STEP/STL export)
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import cadquery as cq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *          # noqa
import arms
import base
import body
import core
import head
import refs
import shells

OUT = Path(__file__).resolve().parents[1] / ("out_fijo" if FIJO else "out")
CACHE = OUT / "cache"
CREAM = (0.95, 0.92, 0.86)
ORANGE = (0.95, 0.42, 0.10)
PEACH = (0.99, 0.74, 0.56)
VISOR = (0.07, 0.08, 0.10)
GREY = (0.60, 0.63, 0.67)
DARKGREY = (0.36, 0.38, 0.42)

# name, builder, colour, group, print-orientation (rotation axis, deg) applied before STL export
PRINTED = [
    ("B1_Base_Cover", base.cover, PEACH, "base", None),
    ("B2_Base_Floor", base.floor, GREY, "base", None),
    ("B3_Battery_Drawer", base.drawer, PEACH, "base", None),
    ("B4_Gimbal_Post", base.post, GREY, "base", None),
    ("G1_Ujoint_Cross", base.cross, DARKGREY, "gimbal", None),
    ("G2_Crank_L", lambda: base.crank("servo_gimbal_L"), DARKGREY, "base", None),
    ("G3_Crank_R", lambda: base.crank("servo_gimbal_R"), DARKGREY, "base", None),
    ("K1_Core_Deck", core.deck, GREY, "core", None),
    ("K2_Core_Spine", core.spine, GREY, "core", None),
    ("K3_Core_Shoulders", core.bridge, GREY, "core", None),
    ("K4_Neck_Hub", core.neck_hub, DARKGREY, "core", None),
    ("K5_Power_Rack", core.power_rack, GREY, "core", None),
    ("S1_Body_Front", lambda: shells.shell("front"), CREAM, "shell", None),
    ("S2_Body_Back", lambda: shells.shell("back"), CREAM, "shell", None),
    ("S3_Tummy_Grille", shells.tummy_grille, ORANGE, "shell", None),
    ("S4_USB_Plug", shells.usb_plug, ORANGE, "shell", None),
    ("A1_Arm_L", lambda: arms.arm(-1), CREAM, "arms", None),
    ("A2_Arm_R", lambda: arms.arm(1), CREAM, "arms", None),
    ("A3_Hand_L", lambda: arms.hand(-1), ORANGE, "arms", None),
    ("A4_Hand_R", lambda: arms.hand(1), ORANGE, "arms", None),
    ("A5_Arm_Cap_L", lambda: arms.cap(-1), ORANGE, "arms", None),
    ("A6_Arm_Cap_R", lambda: arms.cap(1), ORANGE, "arms", None),
    ("H1_Head_Front", lambda: head.shell("front"), CREAM, "head", None),
    ("H2_Head_Back", lambda: head.shell("back"), CREAM, "head", None),
    ("H3_Visor", head.visor, VISOR, "head", None),
    ("H4_Display_Bars", head.display_bars, GREY, "head", None),
    ("H5_Head_Base", head.head_base, GREY, "head", None),
    ("H6_Ear_L", lambda: head.ear(-1), ORANGE, "head", None),
    ("H7_Ear_R", lambda: head.ear(1), ORANGE, "head", None),
    ("H8_Antenna", head.antenna, ORANGE, "head", None),
]
if FIJO:   # fixed variant: pedestal instead of the nest + gimbal, flat deck, flat-bottomed body
    import pedestal
    _swap = {
        "B1_Base_Cover": ("B1_Pedestal", pedestal.shell),
        "B2_Base_Floor": ("B2_Pedestal_Floor", pedestal.floor),
        "B3_Battery_Drawer": ("B3_Pedestal_Drawer", pedestal.drawer),
        "B4_Gimbal_Post": ("B4_Deck_Riser", pedestal.riser),
        "K1_Core_Deck": ("K1_Core_Deck_Fixed", core.deck),
        "S1_Body_Front": ("S1_Body_Front_Fixed", lambda: shells.shell("front")),
        "S2_Body_Back": ("S2_Body_Back_Fixed", lambda: shells.shell("back")),
    }
    PRINTED = [(_swap[n][0], _swap[n][1], c, g, o) if n in _swap else (n, f, c, g, o)
               for n, f, c, g, o in PRINTED if not n.startswith(("G1_", "G2_", "G3_"))]


def world(shape):
    """Build frame -> file frame: the fixed variant's table is at z = GROUND while building."""
    return shape.translate(V(0, 0, -pedestal.GROUND)) if FIJO else shape


def cached(name, fn):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{name}.brep"
    redo = [a.split("=", 1)[1].split(",") for a in sys.argv if a.startswith("--redo=")]
    hit = any(name.startswith(r) for lst in redo for r in lst)
    if f.exists() and "--rebuild" not in sys.argv and not hit:
        return cq.Shape.importBrep(str(f))
    s = fn()
    s.exportBrep(str(f))
    return s


def purchased():
    items = []
    add = lambda lst, grp: items.extend([(n, s, c, grp) for n, s, c in lst])
    add(refs.carrier_pcb(), "electronics")
    add(refs.raspberry_pi5(), "electronics")
    add(refs.power_modules(), "electronics")
    add(refs.speaker(), "electronics")
    add(refs.imu(), "electronics")
    add(pedestal.battery_refs() if FIJO else refs.battery(), "base")
    add(refs.switches(pedestal.switch_positions() if FIJO else base.switch_positions()), "base")
    for nm in ("servo_arm_L", "servo_arm_R"):
        add(refs.servo(nm), "core")
    if not FIJO:
        for nm in ("servo_gimbal_L", "servo_gimbal_R"):
            add(refs.servo(nm), "base")
    add(refs.servo("servo_head"), "head")
    add(head.display_ref(), "head")
    add(head.camera_ref(), "head")
    if FIJO:
        # 4 x M3 x 10 pan-head screws holding the deck on the riser (head on the deck top, core in the pilot)
        for k, (x, y) in enumerate(FIXED_SCREWS):
            scr = fuse(cyl(2.8, 2.4, (x, y, DECK_Z1)), cyl(1.1, 10.0, (x, y, DECK_Z1 - 10.0)))
            items.append((f"screw_deck_M3_{k}", scr, (0.2, 0.2, 0.22), "core"))
        add(pedestal.screw_refs(), "base")
        return items
    # push-rods (M3 rod + 2 ball links each) and the two M4 U-joint bolts
    legs = core.leg_points()
    for key, p in legs.items():
        top = V(p.x, p.y, core.LEG_BALL_Z)
        rod = cyl(1.5, top.z - p.z, (p.x, p.y, p.z))
        b1 = sphere(3.2, (p.x, p.y, p.z))
        b2 = sphere(3.2, (top.x, top.y, top.z))
        l1 = cyl(3.6, 14, (p.x, p.y, p.z + 2))
        l2 = cyl(3.6, 14, (top.x, top.y, top.z - 16))
        items.append((f"pushrod_{key}", fuse(rod, b1, b2, l1, l2), (0.80, 0.80, 0.82), "gimbal"))
    # M4 x 30 self-tapping pivots: head outside the front / left cheek, threads in the far cheek
    roll = fuse(cyl(3.8, 2.8, (0, -14.3, base.ROLL_BOLT_Z), (0, 1, 0)), cyl(1.65, 30, (0, -11.5, base.ROLL_BOLT_Z), (0, 1, 0)))
    pitch = fuse(cyl(3.8, 2.8, (-14.3, 0, base.PITCH_BOLT_Z), (1, 0, 0)), cyl(1.65, 30, (-11.5, 0, base.PITCH_BOLT_Z), (1, 0, 0)))
    items.append(("bolt_roll_M4", roll, (0.75, 0.75, 0.78), "gimbal"))
    items.append(("bolt_pitch_M4", pitch, (0.75, 0.75, 0.78), "gimbal"))
    for nm in ("servo_gimbal_L", "servo_gimbal_R"):
        items.append((f"screw_crank_{nm[-1]}", base.crank_screw(nm), (0.2, 0.2, 0.22), "base"))
    return items


def main():
    t0 = time.time()
    OUT.mkdir(exist_ok=True)
    parts = []
    for name, fn, col, grp, orient_ in PRINTED:
        t = time.time()
        s = cached(name, fn)
        parts.append(dict(name=name, shape=s, color=col, group=grp, printed=True))
        print(f"{name:22s} valid={s.isValid()} solids={len(s.Solids())} dims={dims(s)} {time.time()-t:.1f}s", flush=True)
    for n, s, c, g in purchased():
        parts.append(dict(name=n, shape=s, color=c, group=g, printed=False))
    import pickle
    (OUT / "parts_index.json").write_text(json.dumps([{k: v for k, v in p.items() if k != "shape"} for p in parts], indent=1))
    import meshio
    if "--noglb" in sys.argv:
        return parts
    items = [dict(name=p["name"], shape=world(p["shape"]), color=p["color"], group=p["group"]) for p in parts]
    meshio.export_glb(items, str(OUT / "cuty_v17.glb"), tol=0.05, ang=0.12)
    meshio.export_glb(items, str(OUT / "cuty_v17_web.glb"), tol=0.25, ang=0.17)
    print("glb done", round(time.time() - t0, 1))


if __name__ == "__main__":
    main()
