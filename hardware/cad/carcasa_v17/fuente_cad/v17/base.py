"""Base ('Nido'): cushion cover with the concave dish, floor chassis, battery drawer,
gimbal post, U-joint cross and the two servo cranks."""
from __future__ import annotations

import math

import cadquery as cq

from common import (V, C, CZ, DISH_R, DISH_HOLE_R, BASE_R, BASE_RIM_Z, BASE_WALL, box, cbox, cyl, cyl_c,
                    sphere, fuse, cut, spline_socket, place, orient, text_solid, FONT_MED)
import refs

COVER_WALL = 3.0
FLOOR_T = 3.0
FLOOR_R = BASE_R - COVER_WALL - 0.4          # floor sits inside the cover wall
LUG_ANGLES = (270.0, 32.0, 148.0)            # bayonet lugs (deg from +X)
LUG_TURN = 14.0
SWITCH_ANGLES = (90.0 + 76.0, 90.0 - 76.0)    # left (main), right (servos); 90 = back
SWITCH_Z = 22.0
DRAWER_HALF_W = 59.0                         # outer edge of the drawer flanges (run under the rail lips)
DRAWER_WALL_W = 56.6                         # outer face of the drawer side walls
DRAWER_Z = (FLOOR_T, 34.0)
ROLL_BOLT_Z = CZ - 3.0
PITCH_BOLT_Z = CZ + 3.0

# outer cushion profile (r, z), bottom to rim. Printed upright: the bottom is flat across the whole wall
# (2.2 mm on the bed + 0.8 mm chamfer) and the dome is a spline above z = 4.5.
PROFILE = [(85.2, 0.0), (86.0, 0.8), (86.0, 4.5), (86.0, 30.0), (85.2, 39.0), (82.6, 47.5), (77.8, 55.5),
           (71.8, 61.6), (65.6, 65.2)]
CAVITY_45 = (79.6, 47.5)                      # above this point the cavity ceiling rises at 45 deg (no supports)
RIM_R = math.sqrt(DISH_R ** 2 - (CZ - BASE_RIM_Z) ** 2)


def _revolve_profile(pts_rz, close_to_axis=True):
    wp = cq.Workplane("XZ").moveTo(0, pts_rz[0][1])
    wp = wp.lineTo(*pts_rz[0])
    wp = wp.spline(pts_rz[1:], includeCurrent=True)
    if close_to_axis:
        wp = wp.lineTo(0, pts_rz[-1][1]).close()
    return wp.revolve(360, (0, 0, 0), (0, 1, 0)).val()


def cover():
    """Cushion-shaped cover, printed upright on its flat bottom ring. Only the dish hole edge (centre) and the
    drawer opening lintel (back) need supports, both from the build plate."""
    pts = PROFILE[3:] + [(RIM_R + 1.2, BASE_RIM_Z + 0.6)]
    wp = cq.Workplane("XZ").moveTo(0, 0).lineTo(*PROFILE[0]).lineTo(*PROFILE[1]).lineTo(*PROFILE[2])
    end_t = (pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1])
    wp = wp.spline(pts, includeCurrent=True, tangents=[(0, 1), end_t]).lineTo(0, pts[-1][1]).close()
    outer = wp.revolve(360, (0, 0, 0), (0, 1, 0)).val()
    # top cap above the profile end (the rim) is flat at the rim height; remove everything above the dish
    outer = outer.cut(sphere(DISH_R, C))
    outer = outer.cut(cyl(DISH_HOLE_R, 200, (0, 0, -10)))
    # hollow: inner offset of the outer profile + the dish band thickness
    r_in = BASE_R - COVER_WALL
    rc, zc = CAVITY_45
    inner = cq.Workplane("XZ").moveTo(0, -1).lineTo(r_in, -1).lineTo(r_in, 30.0)
    inner = inner.spline([(82.2, 39.0), (rc, zc)], includeCurrent=True, tangents=[(0, 1), (-1, 1)])
    inner = inner.lineTo(rc - 30.0, zc + 30.0).lineTo(0, zc + 30.0).close()
    inner = inner.revolve(360, (0, 0, 0), (0, 1, 0)).val()
    inner = inner.cut(sphere(DISH_R + 2.4, C).fuse(cyl(DISH_R + 2.4, 200, (0, 0, CZ))))
    body = outer.cut(inner)
    # drawer opening (back) and switch holes (sides, towards the back)
    body = body.cut(box(-DRAWER_HALF_W - 1.0, DRAWER_HALF_W + 1.0, 50.0, 100.0, DRAWER_Z[0] - 3.1, DRAWER_Z[1] + 0.4))
    for ang in SWITCH_ANGLES:
        a = math.radians(ang)
        d = (math.cos(a), math.sin(a), 0)
        body = body.cut(cyl_c(10.1, 20, (BASE_R * d[0], BASE_R * d[1], SWITCH_Z), d))
        body = body.cut(cyl(12.5, 6.0, ((BASE_R - 0.4) * d[0], (BASE_R - 0.4) * d[1], SWITCH_Z), d))
    # bayonet L-slots on the inner wall bottom. As modelled (= assembled) each floor lug sits at the closed end
    # of its run, so the drawer opening lines up with the floor rails; the open entry is LUG_TURN degrees before.
    for ang in LUG_ANGLES:
        e = ang - LUG_TURN
        for a0, a1, z0, z1 in ((e - 5.5, e + 5.5, -1, 6.6), (e - 5.5, ang + 5.5, 2.9, 6.4)):
            slot = _ring_sector(BASE_R - COVER_WALL - 0.2, BASE_R - COVER_WALL + 1.6, a0, a1, z0, z1)
            body = body.cut(slot)
    return body.clean()


def _ring_sector(r0, r1, a0, a1, z0, z1):
    wp = (cq.Workplane("XY").workplane(offset=z0)
          .moveTo(r0 * math.cos(math.radians(a0)), r0 * math.sin(math.radians(a0)))
          .lineTo(r1 * math.cos(math.radians(a0)), r1 * math.sin(math.radians(a0)))
          .threePointArc((r1 * math.cos(math.radians((a0 + a1) / 2)), r1 * math.sin(math.radians((a0 + a1) / 2))),
                         (r1 * math.cos(math.radians(a1)), r1 * math.sin(math.radians(a1))))
          .lineTo(r0 * math.cos(math.radians(a1)), r0 * math.sin(math.radians(a1)))
          .threePointArc((r0 * math.cos(math.radians((a0 + a1) / 2)), r0 * math.sin(math.radians((a0 + a1) / 2))),
                         (r0 * math.cos(math.radians(a0)), r0 * math.sin(math.radians(a0))))
          .close().extrude(z1 - z0))
    return wp.val()


# ------------------------------------------------------------------ floor chassis
POST_FLANGE_R = 20.0
POST_R = 14.0


def _servo_wall(name):
    """Vertical mounting wall in front of a gimbal servo's tabs (servo slides in from behind)."""
    o, xd, zd = refs.SERVO_FRAMES[name]
    s = refs.SERVO
    # in servo-local: wall occupies z in [tab_z0-4, tab_z0] (in front of the tab), x over the tab span
    cx = -s["shaft_off"] + s["L"] / 2
    wall = box(cx - s["tab_len"] / 2 - 3, cx + s["tab_len"] / 2 + 0.5, -s["W"] / 2 - 0.0, s["W"] / 2 + 3.0,
               s["tab_z0"] - 4.0, s["tab_z0"])
    win = box(-s["shaft_off"] - 0.4, -s["shaft_off"] + s["L"] + 0.4, -s["W"] / 2 - 5, s["W"] / 2 + 0.4,
              s["tab_z0"] - 5, s["tab_z0"] + 1)
    wall = wall.cut(win)
    for hx, hy in refs.servo_hole_positions():
        wall = wall.cut(cyl(1.25, 10, (hx, hy, s["tab_z0"] - 6)))
    w = place(wall, o, xd, zd)
    # clip to the floor (z >= FLOOR_T) — the servo's lower tab edge sits on the floor
    return w.cut(box(-200, 200, -200, 200, -50, FLOOR_T))


def floor():
    f = cyl(FLOOR_R, FLOOR_T, (0, 0, 0))
    # feet recesses underneath (4 x Ø10 x 1 mm silicone feet)
    for ang in (45, 135, 225, 315):
        a = math.radians(ang)
        f = f.cut(cyl(5.2, 1.0, (64 * math.cos(a), 64 * math.sin(a), -0.01)))
    # bayonet lugs on the rim
    for ang in LUG_ANGLES:
        f = f.fuse(_ring_sector(FLOOR_R - 1.0, BASE_R - COVER_WALL + 1.3, ang - 4.5, ang + 4.5, FLOOR_T, FLOOR_T + 3.0))
        f = f.fuse(_ring_sector(FLOOR_R - 6.0, FLOOR_R + 0.0, ang - 4.5, ang + 4.5, 0, FLOOR_T + 3.0))
    # servo walls + side guides
    for nm in ("servo_gimbal_L", "servo_gimbal_R"):
        f = f.fuse(_servo_wall(nm))
    # post socket: flange pocket ring with 3 screw bosses
    ring = cyl(POST_FLANGE_R + 3.0, 4.0, (0, 0, FLOOR_T)).cut(cyl(POST_FLANGE_R + 0.3, 5.0, (0, 0, FLOOR_T - 0.5)))
    f = f.fuse(ring)
    for k in range(3):
        a = math.radians(90 + 120 * k)
        f = f.cut(cyl(1.7, 10, (16.0 * math.cos(a), 16.0 * math.sin(a), -1)))
        f = f.cut(cyl(3.1, 1.6, (16.0 * math.cos(a), 16.0 * math.sin(a), -0.01)))
    # battery drawer rails (L-profile) along +Y
    keep = cyl(BASE_R - COVER_WALL - 0.6, 30, (0, 0, -1))
    for sx in (-1, 1):
        x_in = sx * (DRAWER_HALF_W + 0.3)
        x_lip = sx * (DRAWER_WALL_W + 0.3)
        rail = box(min(x_in, x_in + sx * 3.5), max(x_in, x_in + sx * 3.5), 20.0, 80.0, FLOOR_T, FLOOR_T + 7.0)
        lip = box(min(x_in, x_lip), max(x_in, x_lip), 20.0, 80.0, FLOOR_T + 4.2, FLOOR_T + 7.0)
        f = f.fuse(fuse(rail, lip).intersect(keep))
    # drawer stop (merges with the post ring) + detent
    f = f.fuse(box(-30, 30, 20.6, 23.0, FLOOR_T, FLOOR_T + 6))
    f = f.fuse(cyl_c(1.2, 10, (0, 69.0, FLOOR_T + 0.2), (1, 0, 0)))
    # cable tie anchors near the post (battery pigtail + servo leads go up through the dish hole)
    for x in (-24.0, 24.0):
        anc = box(x - 4, x + 4, 6.0, 12.0, FLOOR_T, FLOOR_T + 6).cut(box(x - 5, x + 5, 7.5, 10.5, FLOOR_T + 1.5, FLOOR_T + 3.5))
        f = f.fuse(anc)
    # name underneath (reads correctly with the base flipped over)
    f = f.cut(text_solid("C.U.T.Y  ·  V17 Nido", 7.0, (0, 34.0, 0.6), (1, 0, 0), (0, 0, -1), 0.61, FONT_MED))
    return f.clean()


def drawer():
    """Battery tray: slides in from the back on the floor rails; its face completes the cushion."""
    bx, by, bz = refs.BATT
    cyb = refs.BATT_C[1]
    y0, y1 = cyb - by / 2 - 2.6, cyb + by / 2 + 2.6
    W = DRAWER_WALL_W
    tray = box(-W, W, y0, y1, FLOOR_T + 0.2, FLOOR_T + 1.8)
    walls = box(-W, W, y0, y1, FLOOR_T + 0.2, FLOOR_T + 13.0).cut(
        box(-W + 1.8, W - 1.8, y0 + 1.8, y1 - 1.8, FLOOR_T + 1.8, 50))
    walls = walls.cut(box(-W - 1, -W + 2.5, cyb - 11.5, cyb - 0.5, FLOOR_T + 6.0, 50))      # battery lead notch
    flanges = fuse(box(-DRAWER_HALF_W, -DRAWER_HALF_W + 3.0, y0, 80.0, FLOOR_T + 0.2, FLOOR_T + 3.8),
                   box(DRAWER_HALF_W - 3.0, DRAWER_HALF_W, y0, 80.0, FLOOR_T + 0.2, FLOOR_T + 3.8))
    flanges = flanges.intersect(cyl(BASE_R - COVER_WALL - 0.6, 30, (0, 0, -1)))
    t = fuse(tray, walls, flanges)
    # strap slots for a 20 mm hook-and-loop strap
    for x in (-30.0, 30.0):
        t = t.cut(box(x - 1.6, x + 1.6, cyb - 11, cyb + 11, FLOOR_T - 1, FLOOR_T + 3))
    # curved face matching the cover (r = BASE_R) between the opening edges
    face = cyl(BASE_R, DRAWER_Z[1] - DRAWER_Z[0] - 0.6, (0, 0, DRAWER_Z[0] + 0.1)).cut(
        cyl(BASE_R - COVER_WALL, 60, (0, 0, -1)))
    face = face.intersect(box(-DRAWER_HALF_W - 0.6, DRAWER_HALF_W + 0.6, 40, 100, 0, 60))
    face = face.cut(box(-12, 12, 80, 100, DRAWER_Z[0] + 0.1, DRAWER_Z[0] + 6))        # finger pull
    back = box(-W, W, y1, 81.0, FLOOR_T + 0.2, DRAWER_Z[1] - 0.5).intersect(
        cyl(BASE_R - COVER_WALL + 0.2, 60, (0, 0, -1)))
    back = back.cut(box(-W + 1.8, W - 1.8, y1 - 1, 80.0 - 1.8, FLOOR_T + 1.8, 60))
    t = fuse(t, face, back)
    t = t.cut(cyl_c(1.4, 200, (0, 69.0, FLOOR_T + 0.2), (1, 0, 0)))            # detent groove
    return t.clean()


def post():
    """Gimbal post: flange screwed to the floor, tube, fork holding the roll bolt (Y axis)."""
    flange = cyl(POST_FLANGE_R, 4.0, (0, 0, FLOOR_T))
    tube = cyl(POST_R, ROLL_BOLT_Z - 9 - (FLOOR_T + 4), (0, 0, FLOOR_T + 4))
    neck = cyl(POST_R, 3.0, (0, 0, ROLL_BOLT_Z - 12))
    cheeks = fuse(box(-5.0, 5.0, 7.5, 11.5, ROLL_BOLT_Z - 12, ROLL_BOLT_Z + 8),
                  box(-5.0, 5.0, -11.5, -7.5, ROLL_BOLT_Z - 12, ROLL_BOLT_Z + 8))
    p = fuse(flange, tube, neck, cheeks)
    p = cq.Workplane().add(p).val()
    p = p.cut(cyl(2.15, 20, (0, -20, ROLL_BOLT_Z), (0, 1, 0)))     # M4 x 30 self-tapping: free in the front cheek
    p = p.cut(cyl(1.7, 20, (0, 0, ROLL_BOLT_Z), (0, 1, 0)))        # ... and threads into the back cheek
    p = p.cut(cyl(POST_R - 3.0, 200, (0, 0, -1)).cut(box(-50, 50, -50, 50, ROLL_BOLT_Z - 13, 200)))
    for k in range(3):
        a = math.radians(90 + 120 * k)
        p = p.cut(cyl(1.25, 10, (16.0 * math.cos(a), 16.0 * math.sin(a), FLOOR_T - 1)))
    # cable slot in the tube for the gimbal servo leads
    p = p.cut(box(-4, 4, -20, 0, FLOOR_T + 8, FLOOR_T + 30))
    return p.clean()


def cross():
    c = cbox(0, 0, CZ, 14.0, 14.0, 14.0)
    c = cq.Workplane().add(c).edges().chamfer(1.0).val()
    c = c.cut(cyl_c(2.15, 30, (0, 0, ROLL_BOLT_Z), (0, 1, 0)))
    c = c.cut(cyl_c(2.15, 30, (0, 0, PITCH_BOLT_Z), (1, 0, 0)))
    return c


CRANK_R = 12.0
CRANK_HUB_H = 6.5                  # 3.3 mm spline socket + 3.2 mm floor under the M3 x 8 screw head


def crank(name):
    """Printed crank on the gimbal servo spline: 25T socket + M3 screw, ball stud at r=12."""
    s = refs.SERVO
    hub = cyl(6.0, CRANK_HUB_H, (0, 0, s["boss_h"] + 0.1))
    arm = box(0, CRANK_R + 4.0, -4.0, 4.0, s["boss_h"] + 0.1, s["boss_h"] + 5.1)
    tip = cyl(4.0, 5.0, (CRANK_R, 0, s["boss_h"] + 0.1))
    c = fuse(hub, arm, tip)
    c = c.cut(spline_socket(3.3, (0, 0, s["boss_h"] + 0.1)))
    c = c.cut(cyl(1.7, 10, (0, 0, 0)))
    c = c.cut(cyl(1.25, 10, (CRANK_R, 0, 0)))                   # M3 ball stud thread (self-tap)
    o, xd, zd = refs.SERVO_FRAMES[name]
    # crank arm points towards the robot centre (the case extends the same way)
    return place(c, o, xd, zd)


def crank_screw(name):
    """M3 x 8 machine screw head on top of the crank hub (for clearance checks)."""
    s = refs.SERVO
    h = cyl(2.75, 3.0, (0, 0, s["boss_h"] + 0.1 + CRANK_HUB_H))
    o, xd, zd = refs.SERVO_FRAMES[name]
    return place(h, o, xd, zd)


def crank_tip(name):
    """World position of the ball centre on the crank (ball stud ~6 mm behind the crank face)."""
    s = refs.SERVO
    return refs.servo_point(name, (CRANK_R, 0, s["boss_h"] + 5.1 + 4.0))


def switch_positions():
    out = {}
    for nm, ang in zip(("switch_main", "switch_servos"), SWITCH_ANGLES):
        a = math.radians(ang)
        d = (math.cos(a), math.sin(a), 0.0)
        out[nm] = ((BASE_R * d[0], BASE_R * d[1], SWITCH_Z), d)
    return out
