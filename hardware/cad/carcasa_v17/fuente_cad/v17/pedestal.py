"""Fixed variant ('Fijo'): low pedestal under a flat-bottomed body.

Without the gimbal the body no longer needs its ball, so the shells end flat at PED_CUT and the body stands on a
puck that only holds what the old nest held: the battery drawer and the two switches. Everything above the deck
is the same as the gimbal version, built in the same frame, so the table sits at z = GROUND here; exports shift the
whole robot down by GROUND so the table is z = 0 in every file.

Parts: B1 pedestal (prints upside down, top on the bed), B2 floor (bayonet, carries the drawer rails),
B3 drawer (battery lengthwise, slides out the back), B4 riser (pedestal top -> deck underside).
"""
from __future__ import annotations

import math

import cadquery as cq

from common import (V, PED_CUT, DECK_Z0, FIXED_SCREWS, box, cyl, cyl_c, rbox, fuse, text_solid, FONT_MED)
import refs

# ----------------------------------------------------------------- dimensions (heights are above the table)
PED_R = 63.0                    # outer radius: inside the arms (their inner faces are at |x| = 65.6)
PED_WALL = 3.0
R_IN = PED_R - PED_WALL
FLOOR_T = 3.0
FLOOR_R = R_IN - 0.4
PLATE_T = 3.0
TRAY_Z, TRAY_T = FLOOR_T + 0.2, 1.6
BATT_LEN, BATT_W, BATT_H = refs.BATT          # 108 x 35 x 25: lengthwise along Y here
BATT_MAX_LEN = 109.0                          # longest pack the drawer takes
PED_H = TRAY_Z + TRAY_T + BATT_H + 1.2 + PLATE_T      # 34.0 with a 25 mm pack
PED_TOP = PED_CUT - 0.3                       # 0.3 mm under the body's flat bottom
GROUND = PED_TOP - PED_H                      # table level in the build frame
PLATE_Z0 = PED_TOP - PLATE_T                  # underside of the top plate

# battery: back end as far back as the drawer face allows, the leads leave the front end
_HW = BATT_W / 2
BATT_Y1 = math.sqrt((R_IN - 0.5) ** 2 - _HW ** 2) - 0.25
BATT_C = (0.0, BATT_Y1 - BATT_LEN / 2, GROUND + TRAY_Z + TRAY_T + BATT_H / 2)
DRW_W = _HW + 0.5 + 1.8                       # outer face of the drawer side walls
DRW_HALF = DRW_W + 2.4                        # outer edge of the drawer flanges (run under the rail lips)
DRW_Y0 = BATT_Y1 - BATT_MAX_LEN - 0.3 - 1.5   # front face of the drawer's front lip
FACE_Z = (TRAY_Z, PED_H - PLATE_T - 0.4)
OPEN_HALF = DRW_HALF + 1.0                    # half-width of the drawer opening in the wall
DETENT_Y = 48.0
DETENT_ZC = TRAY_Z + 0.3 - 1.2                # bump axis: its top stands 0.3 mm above the tray bottom

LUG_ANGLES = (35.0, 145.0, 235.0, 305.0)      # bayonet lugs (deg from +X, 90 = back), clear of the drawer
LUG_TURN = 14.0                               # the pedestal goes on turned +14 deg and twists back to lock
SWITCH_Z = 18.0
RISER_R = 28.5
RISER_SCREWS = [(-22.5, -4.0), (-22.5, 5.0), (22.5, -4.0), (22.5, 5.0)]   # M3 x 12 down into the plate bosses
RISER_CB_Z = PED_TOP + 4.0                    # counterbore floor (screw head seat) in the riser
CABLE_HOLES = [(-38.0, 8.0), (38.0, 8.0)]     # under the deck's cable passages
XT60_BAY = (-40.0, -27.0, -36.0, -10.0)       # x0, x1, y0, y1: battery pigtail + extension plug, left bay


def _z(h):
    return GROUND + h


def _ring_sector(r0, r1, a0, a1, z0, z1):
    a0r, a1r, amr = math.radians(a0), math.radians(a1), math.radians((a0 + a1) / 2)
    wp = (cq.Workplane("XY").workplane(offset=z0)
          .moveTo(r0 * math.cos(a0r), r0 * math.sin(a0r))
          .lineTo(r1 * math.cos(a0r), r1 * math.sin(a0r))
          .threePointArc((r1 * math.cos(amr), r1 * math.sin(amr)), (r1 * math.cos(a1r), r1 * math.sin(a1r)))
          .lineTo(r0 * math.cos(a1r), r0 * math.sin(a1r))
          .threePointArc((r0 * math.cos(amr), r0 * math.sin(amr)), (r0 * math.cos(a0r), r0 * math.sin(a0r)))
          .close().extrude(z1 - z0))
    return wp.val()


def switch_positions():
    """Main switch on the left, servo switch on the right, on the pedestal's sides under the arms."""
    return {"switch_main": ((-PED_R, 0.0, _z(SWITCH_Z)), (-1.0, 0.0, 0.0)),
            "switch_servos": ((PED_R, 0.0, _z(SWITCH_Z)), (1.0, 0.0, 0.0))}


# ----------------------------------------------------------------- B1 pedestal
def shell():
    """Puck with a closed top. Printed upside down: the top plate is the first layer, the drawer opening is a
    notch from the open rim, so it needs no supports."""
    g = GROUND
    prof = [(0, g), (PED_R - 0.6, g), (PED_R, g + 0.6), (PED_R, g + PED_H - 3.0), (PED_R - 3.0, g + PED_H),
            (0, g + PED_H)]
    wp = cq.Workplane("XZ").moveTo(*prof[0])
    for p in prof[1:]:
        wp = wp.lineTo(*p)
    p = wp.close().revolve(360, (0, 0, 0), (0, 1, 0)).val()
    p = p.cut(cyl(R_IN, PLATE_Z0 - g + 1.0, (0, 0, g - 1.0)))
    # two ribs under the plate (beside the battery) with the bosses for the riser screws
    for x0, x1 in ((-23.9, -21.1), (21.1, 23.9)):
        p = p.fuse(box(x0, x1, -45.0, 45.0, PLATE_Z0 - 6.5, PLATE_Z0 + 0.01))
    for x, y in RISER_SCREWS:
        p = p.fuse(cyl(3.5, 6.5 + 0.01, (x, y, PLATE_Z0 - 6.5)))
        p = p.cut(cyl(1.25, 20.0, (x, y, PLATE_Z0 - 5.6)))
    # cable holes up into the body, under the deck's own passages
    for x, y in CABLE_HOLES:
        p = p.cut(rbox(x, y, PED_TOP - PLATE_T / 2, 16.0, 24.0, PLATE_T + 2.0, 4.0))
    # drawer opening at the back: from the open rim up to the plate
    y_wall = math.sqrt(R_IN ** 2 - OPEN_HALF ** 2) - 1.0
    p = p.cut(box(-OPEN_HALF, OPEN_HALF, y_wall, PED_R + 5.0, g - 1.0, PLATE_Z0))
    # switch holes (Ø20 rockers) with a 0.4 mm seat for the bezel
    for (pt, d) in switch_positions().values():
        p = p.cut(cyl_c(10.1, 20.0, pt, d))
        p = p.cut(cyl(12.5, 6.0, (pt[0] - d[0] * 0.4, pt[1], pt[2]), d))
    # bayonet L-slots on the inner wall at the open rim. As modelled (= assembled) each floor lug sits at the
    # closed end of its run; the open entry is LUG_TURN degrees before it.
    for ang in LUG_ANGLES:
        e = ang - LUG_TURN
        for a0, a1, z0, z1 in ((e - 5.5, e + 5.5, -1.0, 6.6), (e - 5.5, ang + 5.5, 2.9, 6.4)):
            p = p.cut(_ring_sector(R_IN - 0.2, R_IN + 1.6, a0, a1, g + z0, g + z1))
    return p.clean()


# ----------------------------------------------------------------- B2 floor
def floor():
    g = GROUND
    f = cyl(FLOOR_R, FLOOR_T, (0, 0, g))
    for ang in (45, 135, 225, 315):                       # 4 x Ø10 silicone feet, 1 mm recesses
        a = math.radians(ang)
        f = f.cut(cyl(5.2, 1.0, (46.0 * math.cos(a), 46.0 * math.sin(a), g - 0.01)))
    for ang in LUG_ANGLES:                                # bayonet lugs
        f = f.fuse(_ring_sector(FLOOR_R - 1.0, R_IN + 1.3, ang - 4.5, ang + 4.5, g + FLOOR_T, g + FLOOR_T + 3.0))
        f = f.fuse(_ring_sector(FLOOR_R - 6.0, FLOOR_R, ang - 4.5, ang + 4.5, g, g + FLOOR_T + 3.0))
    keep = cyl(R_IN - 0.6, 30, (0, 0, g - 1))
    for sx in (-1, 1):                                    # drawer rails (L-profile) along Y
        x_in, x_lip = sx * (DRW_HALF + 0.3), sx * (DRW_W + 0.3)
        rail = box(min(x_in, x_in + sx * 3.5), max(x_in, x_in + sx * 3.5), -58.0, 58.0, g + FLOOR_T, g + FLOOR_T + 7.0)
        lip = box(min(x_in, x_lip), max(x_in, x_lip), -58.0, 58.0, g + FLOOR_T + 4.2, g + FLOOR_T + 7.0)
        f = f.fuse(fuse(rail, lip).intersect(keep))
    # drawer stop in front of the lip, detent bump near the back
    f = f.fuse(box(-8.0, 8.0, DRW_Y0 - 1.6, DRW_Y0 - 0.2, g + FLOOR_T, g + FLOOR_T + 6.0))
    for sx in (-1, 1):                                    # detent bumps under the flanges: 0.3 mm lift, inside
        f = f.fuse(cyl_c(1.2, 1.8, (sx * 21.0, DETENT_Y, g + DETENT_ZC), (1, 0, 0)))   # the 0.4 mm lip play
    # cable-tie anchors in the side bays (battery extension left, switch wires right)
    for x in (-47.0, 47.0):
        anc = box(x - 4, x + 4, -31.0, -25.0, g + FLOOR_T, g + FLOOR_T + 6).cut(
            box(x - 5, x + 5, -29.5, -26.5, g + FLOOR_T + 1.5, g + FLOOR_T + 3.5))
        f = f.fuse(anc)
    f = f.cut(text_solid("C.U.T.Y  ·  V17 Fijo", 7.0, (0, -8.0, g + 0.6), (1, 0, 0), (0, 0, -1), 0.61, FONT_MED))
    return f.clean()


# ----------------------------------------------------------------- B3 drawer
def drawer():
    """Battery tray, pack lengthwise. Its back is a piece of the pedestal wall; the front lip is low so the
    leads leave the pack's front end and fold into the left bay."""
    W, cy = DRW_W, BATT_C[1]
    zt0, zt1 = _z(TRAY_Z), _z(TRAY_Z + TRAY_T)
    inside = cyl(R_IN + 1.0, 60, (0, 0, GROUND - 5))
    tray = box(-W, W, DRW_Y0, PED_R, zt0, zt1)
    walls = box(-W, W, DRW_Y0, PED_R, zt0, _z(TRAY_Z + 13.0)).cut(
        box(-W + 1.8, W - 1.8, DRW_Y0 + 1.5, PED_R + 5, zt1, _z(60)))
    walls = walls.cut(box(-W + 1.8, W - 1.8, DRW_Y0 - 1, DRW_Y0 + 2, _z(TRAY_Z + 7.0), _z(60)))   # low front lip
    flanges = fuse(box(-DRW_HALF, -DRW_HALF + 3.0, DRW_Y0, PED_R, zt0, _z(TRAY_Z + 3.6)),
                   box(DRW_HALF - 3.0, DRW_HALF, DRW_Y0, PED_R, zt0, _z(TRAY_Z + 3.6)))
    flanges = flanges.intersect(cyl(R_IN - 0.6, 60, (0, 0, GROUND - 5)))
    t = fuse(tray, walls).intersect(inside).fuse(flanges)
    for y in (cy - 30.0, cy + 30.0):                      # slots for a 20 mm hook-and-loop strap
        t = t.cut(box(-11.0, 11.0, y - 1.6, y + 1.6, zt0 - 1, zt1 + 1))
    # face: the piece of pedestal wall that closes the opening
    face = cyl(PED_R, FACE_Z[1] - FACE_Z[0], (0, 0, _z(FACE_Z[0]))).cut(cyl(R_IN, 80, (0, 0, GROUND - 5)))
    face = face.intersect(box(-OPEN_HALF + 0.6, OPEN_HALF - 0.6, 30.0, 100.0, GROUND - 5, _z(60)))
    face = face.cut(box(-12.0, 12.0, 30.0, 100.0, _z(FACE_Z[0]) - 1, _z(FACE_Z[0] + 6.0)).cut(
        cyl(R_IN - 0.01, 80, (0, 0, GROUND - 5))))          # finger pull
    t = fuse(t, face)
    t = t.cut(cyl_c(1.4, 200, (0, DETENT_Y, _z(DETENT_ZC)), (1, 0, 0)))   # detent groove (flange bottoms)
    return t.clean()


# ----------------------------------------------------------------- B4 riser
def riser():
    """Drum from the pedestal top to the deck underside. 4 x M3 x 12 down into the plate bosses (heads in
    counterbores), then the deck on top with 4 x M3 x 10."""
    z0 = PED_TOP
    r = cyl(RISER_R, DECK_Z0 - z0, (0, 0, z0)).cut(cyl(12.0, 100, (0, 0, z0 - 1)))
    for x, y in FIXED_SCREWS:
        r = r.cut(cyl(1.25, 9.0, (x, y, DECK_Z0 - 8.5)))
    for x, y in RISER_SCREWS:
        r = r.cut(cyl(1.7, 10.0, (x, y, z0 - 1.0)))
        r = r.cut(cyl(3.1, 30.0, (x, y, RISER_CB_Z)))
    return r.clean()


# ----------------------------------------------------------------- purchased parts in the pedestal
def battery_refs():
    b = cq.Solid.makeBox(BATT_W, BATT_LEN, BATT_H, V(BATT_C[0] - _HW, BATT_C[1] - BATT_LEN / 2, BATT_C[2] - BATT_H / 2))
    b = cq.Workplane().add(b).edges("|Y").fillet(3).val()
    y0 = BATT_C[1] - BATT_LEN / 2
    lead = box(-14.0, -4.0, y0 - 5.0, y0, BATT_C[2] - 4.0, BATT_C[2] + 6.0)       # main + balance leads, front end
    x0, x1, yb0, yb1 = XT60_BAY
    plug = box(x0, x1, yb0, yb1, _z(FLOOR_T + 0.2), _z(15.0))                     # XT60 pair + slack, left bay
    return [("battery_3s_2200", b, refs.COL["battery"]), ("battery_lead", lead, (0.8, 0.15, 0.12)),
            ("xt60_joint", plug, (0.85, 0.75, 0.15))]


def screw_refs():
    out = []
    for k, (x, y) in enumerate(RISER_SCREWS):
        s = fuse(cyl(2.8, 2.4, (x, y, RISER_CB_Z)), cyl(1.1, 12.0, (x, y, RISER_CB_Z - 12.0)))
        out.append((f"screw_riser_M3x12_{k}", s, (0.2, 0.2, 0.22)))
    return out
