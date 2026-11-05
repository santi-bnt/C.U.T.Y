"""Static interference, motion sweeps and print-bed fit for C.U.T.Y V17."""
from __future__ import annotations

import itertools
import json
import math
import sys
import time
from pathlib import Path

import cadquery as cq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *   # noqa
import base, build, core, refs, head, arms, shells

OUT = build.OUT


def load_parts():
    parts = []
    for name, fn, col, grp, _ in build.PRINTED:
        parts.append(dict(name=name, shape=build.cached(name, fn), group=grp, printed=True))
    for n, s, c, g in build.purchased():
        parts.append(dict(name=n, shape=s, group=g, printed=False))
    return parts


def bb_overlap(a, b, m=0.0):
    A, B = a.BoundingBox(), b.BoundingBox()
    return not (A.xmax + m < B.xmin or B.xmax + m < A.xmin or A.ymax + m < B.ymin or B.ymax + m < A.ymin
                or A.zmax + m < B.zmin or B.zmax + m < A.zmin)


def inter_vol(a, b):
    try:
        i = a.intersect(b)
        return i.Volume() if not i.isNull() else 0.0
    except Exception as e:
        return -1.0


IGNORE = [  # intended contacts / press fits
    ("_spline", "G2_Crank"), ("_spline", "G3_Crank"), ("_spline", "A1_Arm"), ("_spline", "A2_Arm"), ("_spline", "K4_Neck_Hub"),
    ("pushrod", "K1_Core_Deck"), ("pushrod", "G2_Crank"), ("pushrod", "G3_Crank"),
]


def ignored(a, b):
    for x, y in IGNORE:
        if (x in a and y in b) or (x in b and y in a):
            return True
    return False


MOVING_GROUPS = {"core", "shell", "arms", "head", "electronics"}


def static_check(parts, tol=0.5):
    res = []
    for p, q in itertools.combinations(parts, 2):
        if not (p["printed"] or q["printed"]):
            continue
        if ignored(p["name"], q["name"]):
            continue
        if not bb_overlap(p["shape"], q["shape"]):
            continue
        v = inter_vol(p["shape"], q["shape"])
        if v > tol or v < 0:
            res.append((p["name"], q["name"], round(v, 2)))
    return res


def keepout_check(parts):
    kos = refs.carrier_keepouts() + refs.pi_keepouts() + refs.power_keepouts() + [("ko_lcd_header", head.display_keepout())]
    res = []
    for n, k in kos:
        for p in parts:
            if not p["printed"] or not bb_overlap(k, p["shape"]):
                continue
            v = inter_vol(k, p["shape"])
            if v > 0.5:
                res.append((n, p["name"], round(v, 2)))
    return res


def body_transform(shape, pitch, roll):
    s = shape.rotate(V(0, 0, base.PITCH_BOLT_Z), V(1, 0, base.PITCH_BOLT_Z), pitch)
    return s.rotate(V(0, 0, base.ROLL_BOLT_Z), V(0, 1, base.ROLL_BOLT_Z), roll)


def gimbal_sweep(parts):
    moving = [p for p in parts if p["group"] in MOVING_GROUPS]
    static = [p for p in parts if p["group"] in ("base",) and not p["name"].startswith("pushrod")]
    res = {}
    for pitch, roll in ((18, 0), (-18, 0), (0, 18), (0, -18), (13, 13), (-13, -13), (13, -13), (-13, 13)):
        hits = []
        for m in moving:
            ms = body_transform(m["shape"], pitch, roll)
            for s in static:
                if not bb_overlap(ms, s["shape"]):
                    continue
                v = inter_vol(ms, s["shape"])
                if v > 0.5 or v < 0:
                    hits.append((m["name"], s["name"], round(v, 2)))
        res[f"pitch{pitch:+d}_roll{roll:+d}"] = hits
    return res


def head_sweep(parts):
    hp = [p for p in parts if p["group"] == "head" and p["name"] != "servo_head_spline"]
    others = [p for p in parts if p["group"] in ("shell", "arms", "core") and p["name"] != "K4_Neck_Hub"]
    res = {}
    for ang in (-90, -45, 45, 90):
        hits = []
        for h in hp:
            hs = h["shape"].rotate(V(0, 0, 0), V(0, 0, 1), ang)
            for o in others:
                if not bb_overlap(hs, o["shape"]):
                    continue
                v = inter_vol(hs, o["shape"])
                if v > 0.5 or v < 0:
                    hits.append((h["name"], o["name"], round(v, 2)))
        res[f"pan{ang:+d}"] = hits
    return res


def arm_sweep(parts):
    res = {}
    names = {-1: ("A1_Arm_L", "A3_Hand_L", "A5_Arm_Cap_L"), 1: ("A2_Arm_R", "A4_Hand_R", "A6_Arm_Cap_R")}
    others = [p for p in parts if p["group"] in ("shell", "head", "base")]
    for sx, nms in names.items():
        ap = [p for p in parts if p["name"] in nms]
        for ang in (-120, -60, 60, 120):
            hits = []
            for a in ap:
                s = a["shape"].rotate(V(0, ARM_AXIS_Y, ARM_AXIS_Z), V(1, ARM_AXIS_Y, ARM_AXIS_Z), ang)
                for o in others:
                    if not bb_overlap(s, o["shape"]):
                        continue
                    v = inter_vol(s, o["shape"])
                    if v > 0.5 or v < 0:
                        hits.append((a["name"], o["name"], round(v, 2)))
            res[f"arm{'L' if sx < 0 else 'R'}{ang:+d}"] = hits
    return res


def bed_fit(parts):
    out = {}
    for p in parts:
        if not p["printed"]:
            continue
        d = sorted(dims(p["shape"]))
        out[p["name"]] = dict(dims=d, fits_180=all(x <= 180 for x in d), valid=p["shape"].isValid(),
                              solids=len(p["shape"].Solids()), volume_cm3=round(p["shape"].Volume() / 1000, 1))
    return out


def main():
    t = time.time()
    parts = load_parts()
    rep = {}
    rep["bed_fit"] = bed_fit(parts)
    print("bed fit done", round(time.time() - t), flush=True)
    rep["static"] = static_check(parts)
    print("static", rep["static"], round(time.time() - t), flush=True)
    rep["keepouts"] = keepout_check(parts)
    print("keepouts", rep["keepouts"], round(time.time() - t), flush=True)
    if "--static" not in sys.argv:
        rep["gimbal"] = gimbal_sweep(parts)
        print("gimbal", json.dumps(rep["gimbal"]), round(time.time() - t), flush=True)
        rep["head_pan"] = head_sweep(parts)
        print("head", json.dumps(rep["head_pan"]), round(time.time() - t), flush=True)
        rep["arms"] = arm_sweep(parts)
        print("arms", json.dumps(rep["arms"]), round(time.time() - t), flush=True)
    (OUT / "verify_report.json").write_text(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
