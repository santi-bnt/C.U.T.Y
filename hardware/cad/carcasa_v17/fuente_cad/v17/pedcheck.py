"""Fixed variant: exact checks for the pedestal (CUTY_FIJO=1 python3 pedcheck.py).

- every pair among the pedestal parts, the deck, the riser/deck screws and the parts bought for the pedestal
  (battery, leads, XT60 joint, switches), including bought-vs-bought;
- the drawer (with the battery) pulled out the back in 5 mm steps;
- the bayonet: the pedestal turned back towards its entry in 2 deg steps, then lifted off at the entry;
- the body shells slid off horizontally over the pedestal.
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import V, FIJO   # noqa
import build
import pedestal

assert FIJO, "run with CUTY_FIJO=1"


def iv(a, b):
    A, B = a.BoundingBox(), b.BoundingBox()
    if A.xmax < B.xmin or B.xmax < A.xmin or A.ymax < B.ymin or B.ymax < A.ymin or A.zmax < B.zmin or B.zmax < A.zmin:
        return 0.0
    i = a.intersect(b)
    return 0.0 if i.isNull() else round(i.Volume(), 3)


P = {n: build.cached(n, fn) for n, fn, *_ in build.PRINTED}
B = {n: s for n, s, c, g in build.purchased()}
rep = {}

# 1. pairs in and around the pedestal
names = ["B1_Pedestal", "B2_Pedestal_Floor", "B3_Pedestal_Drawer", "B4_Deck_Riser", "K1_Core_Deck_Fixed",
         "S1_Body_Front_Fixed", "S2_Body_Back_Fixed"]
shapes = {n: P[n] for n in names}
shapes.update({n: s for n, s in B.items() if n.startswith(("battery", "xt60", "switch", "screw_riser", "screw_deck"))})
hits = []
for a, b in itertools.combinations(shapes, 2):
    v = iv(shapes[a], shapes[b])
    if v > 0.0:
        hits.append((a, b, v))
rep["pairs_checked"] = len(list(itertools.combinations(shapes, 2)))
rep["pair_hits"] = hits
print("pairs", rep["pairs_checked"], "hits", hits, flush=True)

# 2. drawer pull-out
moving = [P["B3_Pedestal_Drawer"], B["battery_3s_2200"], B["battery_lead"]]
fixed = {n: shapes[n] for n in shapes if n not in ("B3_Pedestal_Drawer", "battery_3s_2200", "battery_lead", "xt60_joint")}
res, lifted = [], []
for dy in range(5, 135, 5):
    for k, m in enumerate(moving):
        mm = m.translate(V(0, dy, 0))
        for n, f in fixed.items():
            v = iv(mm, f)
            if v > 0.0:
                # the only allowed touch: the flanges riding over the detent bumps, which lift the drawer 0.3 mm
                # (inside the 0.4 mm play under the rail lips)
                if k == 0 and n == "B2_Pedestal_Floor" and iv(mm.translate(V(0, 0, 0.32)), f) == 0.0:
                    lifted.append(dy)
                    continue
                res.append((dy, ["drawer", "battery", "lead"][k], n, v))
rep["drawer_pull"] = dict(hits=res, rides_over_detent_at_mm=lifted)
print("drawer pull 5..130 mm:", res, "detent lift at", lifted, flush=True)

# 3. bayonet: pedestal turned towards its entry (lugs travel along the run), lifted off at the entry
ped, flo = P["B1_Pedestal"], P["B2_Pedestal_Floor"]
res = []
for ang in range(0, int(pedestal.LUG_TURN) + 1, 2):
    r = ped.rotate(V(0, 0, 0), V(0, 0, 1), ang)
    v = iv(r, flo)
    if v > 0.0:
        res.append(("turn", ang, v))
r = ped.rotate(V(0, 0, 0), V(0, 0, 1), pedestal.LUG_TURN)
for dz in (2, 4, 6, 8, 10):
    v = iv(r.translate(V(0, 0, dz)), flo)
    if v > 0.0:
        res.append(("lift", dz, v))
locked = iv(ped.translate(V(0, 0, 1.0)), flo)   # locked: lifting 1 mm must already hit the lugs (they hold)
rep["bayonet"] = dict(hits=res, locked_holds=locked > 0.0)
print("bayonet", res, "locked holds:", locked > 0.0, flush=True)

# 4. body shells slide off horizontally over the pedestal (front shell forward, back shell backward)
res = []
for n, sgn in (("S1_Body_Front_Fixed", -1), ("S2_Body_Back_Fixed", 1)):
    for d in (10, 30, 60, 90):
        v = iv(P[n].translate(V(0, sgn * d, 0)), ped)
        if v > 0.0:
            res.append((n, d, v))
rep["shell_slide"] = res
print("shell slide", res, flush=True)

rep["ground_z"] = round(pedestal.GROUND, 2)
rep["pedestal"] = dict(diameter=2 * pedestal.PED_R, height=pedestal.PED_H)
(build.OUT / "pedcheck.json").write_text(json.dumps(rep, indent=1))
