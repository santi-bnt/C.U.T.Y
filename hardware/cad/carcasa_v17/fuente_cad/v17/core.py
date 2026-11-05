"""Body core (internal chassis): deck, spine, shoulder bridge, power rack, neck hub, collar.

Everything electronic bolts to the core first; the cosmetic shells click on afterwards.
"""
from __future__ import annotations

import math

import cadquery as cq

from common import (V, C, CZ, DECK_Z0, DECK_Z1, DECK_T, SPINE_Y0, SPINE_Y1, ARM_AXIS_Y, ARM_AXIS_Z, BODY_WALL,
                    box, cbox, rbox, cyl, cyl_c, fuse, cut, superellipse_prism, spline_socket, place, rounded_block)
import body
import refs
import base

DECK_CLEAR = 0.8
SPINE_TOP = 194.0
SPINE_X = (-56.0, 53.5)            # right edge leaves a path for the 40-way ribbon to the Pi
BEAM_Z = (194.0, 198.0)
PLATE_X = (54.0, 57.0)             # shoulder plates (outboard of the arm-servo tabs)
PLATE_Y = (-10.0, 18.0)
PLATE_Z = (132.0, 194.0)
LEG_BOTTOM_Z = 58.0
LEG_BALL_Z = 62.0
CLIP_ANGLES = {"front": (-58.0, -122.0, -12.0, -168.0), "back": (28.0, 90.0, 152.0)}   # deg from +X, -90 = front
COLLAR_Z = (206.0, 211.5)
RACK_EARS = [(sx * 16.75, z) for sx in (-1, 1) for z in (136.0, 178.0)]   # side ears beside the buck


def section_prism(z0, z1, extra_offset):
    """Prism following the body's inner section at mid-height, shrunk by extra_offset."""
    # use the narrower end so the prism never touches a wall that flares with height
    pa = body.profile_at(z0, BODY_WALL + extra_offset)
    pb = body.profile_at(z1, BODY_WALL + extra_offset)
    a, b, n = pa if pa[0] < pb[0] else pb
    return superellipse_prism(a, b, n, z0, z1)


def leg_points():
    return {"L": base.crank_tip("servo_gimbal_L"), "R": base.crank_tip("servo_gimbal_R")}


# ------------------------------------------------------------------ deck
def deck():
    d = section_prism(DECK_Z0, DECK_Z1, DECK_CLEAR)
    # speaker clearance at the front, central opening over the U-joint
    d = d.cut(box(-24.0, 24.0, -80.0, -40.5, DECK_Z0 - 1, DECK_Z1 + 1))
    d = d.cut(cbox(0, 0, DECK_Z0, 13.0, 13.0, 3.0))                   # cross clearance pocket
    # cable passages (battery pigtail left, gimbal servo leads right, switch wires)
    for x in (-38.0, 38.0):
        d = d.cut(rounded_block(14.0, 22.0, 10.0, 4.0, 0, (x, 8.0, DECK_Z0 + 1.5)))
    # U-joint fork (pitch bolt along X)
    for sx in (-1, 1):
        ch = box(min(sx * 7.5, sx * 11.5), max(sx * 7.5, sx * 11.5), -5.0, 5.0, base.PITCH_BOLT_Z - 8.0, DECK_Z0 + 0.5)
        d = d.fuse(ch)
    d = d.cut(cyl_c(2.15, 40, (0, 0, base.PITCH_BOLT_Z), (1, 0, 0)))
    # legs carrying the upper ball studs of the push-rods
    for key, p in leg_points().items():
        leg = box(p.x - 4.5, p.x + 4.5, p.y - 11.5, p.y - 3.5, LEG_BOTTOM_Z, DECK_Z0 + 0.5)
        d = d.fuse(leg)
        d = d.cut(cyl_c(1.25, 14, (p.x, p.y - 7.5, LEG_BALL_Z), (0, 1, 0)))   # M3 ball stud, self-tapping
    # spine socket (slot) + 2 screw holes from below
    d = d.cut(box(SPINE_X[0] + 6, SPINE_X[1] - 6, SPINE_Y0 - 0.2, SPINE_Y1 + 0.2, DECK_Z1 - 1.6, DECK_Z1 + 1))
    for x in (-30.0, 30.0):
        d = d.cut(cyl(1.7, 10, (x, (SPINE_Y0 + SPINE_Y1) / 2, DECK_Z0 - 1)))
        d = d.cut(cyl(3.1, 2.0, (x, (SPINE_Y0 + SPINE_Y1) / 2, DECK_Z0 - 0.01)))
    # Raspberry Pi 5 standoffs (M2.5, self-tapping)
    for hx, hy in refs.PI_HOLES:
        p = refs.pi_to_world(hx, hy, -1.6)
        d = d.fuse(cyl(3.0, refs.PI_STANDOFF, (p.x, p.y, DECK_Z1)))
        d = d.cut(cyl(1.05, refs.PI_STANDOFF + 4, (p.x, p.y, DECK_Z1 - 2)))
    # IMU pad (2 x M2.5 standoffs)
    ix, iy, iz = refs.IMU_C
    for dx in (-7.75, 7.75):
        d = d.fuse(cyl(2.4, 2.0, (ix + dx, iy + 5.5, DECK_Z1)))
        d = d.cut(cyl(1.05, 6.0, (ix + dx, iy + 5.5, DECK_Z1 - 2)))
    return d.clean()


def _rim_point(ang, z, offset):
    a, b, n = body.profile_at(z, BODY_WALL + offset)
    t = math.radians(ang)
    c, s = math.cos(t), math.sin(t)
    return (a * math.copysign(abs(c) ** (2 / n), c), b * math.copysign(abs(s) ** (2 / n), s))


def tongue_slot(ang):
    x, y = _rim_point(ang, DECK_Z0 + 1.5, 0.0)
    t = math.atan2(y, x)
    slot = cbox(0, 0, 0, 14.0, 12.4, DECK_T + 1.0)
    slot = slot.rotate(V(0, 0, 0), V(0, 0, 1), math.degrees(t))
    return slot.translate(V(x, y, DECK_Z0 + DECK_T / 2))


# ------------------------------------------------------------------ spine
def spine():
    s = box(SPINE_X[0], SPINE_X[1], SPINE_Y0, SPINE_Y1, DECK_Z1, SPINE_TOP)
    s = cq.Workplane().add(s).edges("|Y").edges(">Z").fillet(6.0).val()
    # tenon into the deck slot
    s = s.fuse(box(SPINE_X[0] + 6.3, SPINE_X[1] - 6.3, SPINE_Y0, SPINE_Y1, DECK_Z1 - 1.5, DECK_Z1 + 0.5))
    # lightening / cable window behind the ReSpeaker (right of the buck)
    s = s.cut(rbox(36.0, (SPINE_Y0 + SPINE_Y1) / 2, 150.0, 14.0, 10.0, 30.0, 5.0, "Y"))
    # carrier PCB standoffs (front), M3 self-tapping
    for hx, hy in refs.PCB_HOLES:
        p = refs.board_to_world(hx, hy)
        s = s.fuse(cyl(3.6, refs.PCB_STANDOFF, (p.x, SPINE_Y0, p.z), (0, -1, 0)))
        s = s.cut(cyl(1.25, 30, (p.x, SPINE_Y1 + 1, p.z), (0, -1, 0)))
    # screw holes for the bridge (top) and deck (bottom)
    for x in (-30.0, 30.0):
        s = s.cut(cyl(1.25, 14, (x, (SPINE_Y0 + SPINE_Y1) / 2, DECK_Z1 - 2)))
        s = s.cut(cyl(1.25, 12, (x, (SPINE_Y0 + SPINE_Y1) / 2, SPINE_TOP - 10)))
    # power rack mount (2 holes)
    for x, z in RACK_EARS:
        s = s.cut(cyl(1.7, 10, (x, SPINE_Y0 - 1, z), (0, 1, 0)))
    # cable notches on the left edge (battery pigtail) and wire comb on the top edge
    s = s.cut(rbox(SPINE_X[0], (SPINE_Y0 + SPINE_Y1) / 2, 160.0, 8.0, 10.0, 18.0, 3.0, "Y"))
    return s.clean()


# ------------------------------------------------------------------ shoulder bridge (arm servos + beam)
def _arm_plate(side):
    sx = 1 if side == "R" else -1
    x0, x1 = sorted((sx * PLATE_X[0], sx * PLATE_X[1]))
    p = box(x0, x1, PLATE_Y[0], PLATE_Y[1], PLATE_Z[0], PLATE_Z[1])
    p = cq.Workplane().add(p).edges("|X").fillet(5.0).val()
    name = f"servo_arm_{side}"
    s = refs.SERVO
    # window for the case (the servo is inserted from inside, tabs rest on the plate)
    o, xd, zd = refs.SERVO_FRAMES[name]
    win = box(-s["shaft_off"] - 0.4, -s["shaft_off"] + s["L"] + 0.4, -s["W"] / 2 - 0.4, s["W"] / 2 + 0.4,
              s["tab_z1"] - 0.1, 8.0)
    p = p.cut(place(win, o, xd, zd))
    for hx, hy in refs.servo_hole_positions():
        q = refs.servo_point(name, (hx, hy, s["tab_z1"]))
        p = p.cut(cyl_c(1.25, 12, (q.x, q.y, q.z), (1, 0, 0)))
    return p


def bridge():
    beam_a, beam_b, beam_n = body.profile_at(BEAM_Z[1] + 1.5, BODY_WALL + 1.8)
    beam = superellipse_prism(beam_a, beam_b, beam_n, BEAM_Z[0], BEAM_Z[1]).intersect(
        box(-60, 60, SPINE_Y0, PLATE_Y[1], BEAM_Z[0], BEAM_Z[1]))
    br = fuse(beam, _arm_plate("R"), _arm_plate("L"))
    # gussets between the plates and the beam
    for sx in (-1, 1):
        g = box(min(sx * 46.0, sx * 54.0), max(sx * 46.0, sx * 54.0), PLATE_Y[0], PLATE_Y[0] + 3.0, 180.0, BEAM_Z[0])
        br = br.fuse(g)
    # neck hub seat + collar posts
    br = br.cut(cyl(1.7, 12, (0, 0, BEAM_Z[0] - 2)))
    for k in range(3):
        a = math.radians(90 + 120 * k)
        hx, hy = 12.5 * math.cos(a), 12.5 * math.sin(a)
        br = br.cut(cyl(1.25, 12, (hx, hy, BEAM_Z[0] - 4)))
    # cable passages through the beam: display ribbon (front), camera FFC (back), servo leads
    br = br.cut(rounded_block(38.0, 7.0, 10.0, 3.0, 0, (0, -9.0 + 0.0, (BEAM_Z[0] + BEAM_Z[1]) / 2)).translate(V(0, 0, 0)))
    br = br.cut(rounded_block(20.0, 6.0, 10.0, 2.5, 0, (0, 14.0, (BEAM_Z[0] + BEAM_Z[1]) / 2)))
    # screws into the spine top
    for x in (-30.0, 30.0):
        br = br.cut(cyl(1.7, 12, (x, (SPINE_Y0 + SPINE_Y1) / 2, BEAM_Z[0] - 2)))
    return br.clean()


def collar_post_points():
    return [(-21.0, 14.0), (21.0, 14.0), (-21.0, -10.5), (21.0, -10.5)]


# ------------------------------------------------------------------ neck hub (fixed spline for the head servo)
def neck_hub():
    h = cyl(11.0, refs.HUB_TOP_Z - BEAM_Z[1], (0, 0, BEAM_Z[1]))
    fl = cyl(16.0, 3.0, (0, 0, BEAM_Z[1]))
    h = fuse(h, fl)
    h = h.cut(spline_socket(3.3, (0, 0, refs.HUB_TOP_Z - 3.3)))
    h = h.cut(cyl(1.7, 30, (0, 0, BEAM_Z[1] - 1)))                         # M3 from below into the spline
    h = h.cut(cyl(3.1, 3.5, (0, 0, BEAM_Z[1] - 0.01)))
    for k in range(3):
        a = math.radians(90 + 120 * k)
        h = h.cut(cyl(1.7, 10, (12.5 * math.cos(a), 12.5 * math.sin(a), BEAM_Z[1] - 1)))
        h = h.cut(cyl(3.0, 2.0, (12.5 * math.cos(a), 12.5 * math.sin(a), BEAM_Z[1] + 1.01)))
    return h.clean()


# ------------------------------------------------------------------ power rack (buck against the spine, regulator behind)
def power_rack():
    bx, by, bz = refs.BUCK_C
    rx, ry, rz = refs.REG_C
    bw, bd, bh = refs.BUCK
    rw, rd, rh = refs.REG
    frame = box(-bw / 2 - 2.5, bw / 2 + 2.5, by + bd / 2, ry - rd / 2, rz - rh / 2 - 2, bz + bh / 2 + 1)
    side_l = box(-bw / 2 - 2.5, -bw / 2 - 0.5, SPINE_Y1, ry + rd / 2, rz - rh / 2 - 2, rz - rh / 2 + 8)
    side_r = box(bw / 2 + 0.5, bw / 2 + 2.5, SPINE_Y1, ry + rd / 2, rz - rh / 2 - 2, rz - rh / 2 + 8)
    shelf = box(-rw / 2 - 2.5, rw / 2 + 2.5, ry - rd / 2, ry + rd / 2, rz - rh / 2 - 2, rz - rh / 2)
    lip = box(-rw / 2 - 2.5, rw / 2 + 2.5, ry + rd / 2, ry + rd / 2 + 2, rz - rh / 2 - 2, rz - rh / 2 + 6)
    # side ears (wires leave the buck terminals upwards, the Pi's IDC plug sits below)
    ears = fuse(*[box(min(sx * (bw / 2 + 0.5), sx * (bw / 2 + 6.5)), max(sx * (bw / 2 + 0.5), sx * (bw / 2 + 6.5)),
                      SPINE_Y1, ry - rd / 2, z - 3.0, z + 3.0) for sx in (-1, 1) for z in (136.0, 178.0)])
    r = fuse(frame, side_l, side_r, shelf, lip, ears)
    for x, z in RACK_EARS:
        r = r.cut(cyl(1.25, 40, (x, SPINE_Y1 - 1, z), (0, 1, 0)))
    # the regulator's USB-C plug leaves downwards through the shelf
    r = r.cut(box(-7.5, 7.5, ry - rd / 2 + 0.5, ry + rd / 2 + 3, rz - rh / 2 - 12, rz - rh / 2 + 0.5))
    for z in (rz - 12, rz + 12):
        r = r.cut(cbox(-bw / 2 - 1.5, (by + bd / 2 + ry - rd / 2) / 2, z, 2.0, 20, 4))
        r = r.cut(cbox(bw / 2 + 1.5, (by + bd / 2 + ry - rd / 2) / 2, z, 2.0, 20, 4))
    r = r.cut(rbox(0, (by + bd / 2 + ry - rd / 2) / 2, bz, bw - 6, 10, bh - 14, 3, "Y"))
    return r.clean()


# ------------------------------------------------------------------ collar (orange accent ring, clamps both shells)
def collar():
    """Orange neck ring: its skirt sits inside both shell tops, the ring presses them down."""
    z0, z1 = COLLAR_Z
    ring = cyl(38.5, z1 - z0 + 4.0, (0, 0, z0 - 4.0))
    ring = ring.cut(body.outer_solid())
    ring = ring.intersect(box(-60, 60, -60, 60, z0 - 4.0, z1))
    ring = cq.Workplane().add(ring).val()
    skirt = cyl(30.2, z1 - z0 + 5.5, (0, 0, z0 - 5.5)).cut(cyl(27.6, 30, (0, 0, z0 - 7)))
    ring = fuse(ring, skirt)
    ring = ring.cut(cyl(21.0, 40, (0, 0, z0 - 10)))
    for px, py in collar_post_points():
        ring = ring.cut(cyl(1.7, 14, (px, py, z0 - 8)))
        ring = ring.cut(cyl(3.0, 2.2, (px, py, z1 - 2.2)))
    try:
        ring = cq.Workplane().add(ring).faces(">Z").edges().fillet(1.2).val()
    except Exception:
        pass
    return ring.clean()
