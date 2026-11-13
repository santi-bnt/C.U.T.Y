"""Body front ('tummy') and back shells.

They slide onto the core horizontally: C-clips catch the deck rim and the shoulder beam.
The two arm hubs pass through the split holes and lock both shells (the arms are the keys).
"""
from __future__ import annotations

import math

import cadquery as cq

from common import (V, CZ, BODY_WALL, ARM_AXIS_Y, ARM_AXIS_Z, DECK_Z0, DECK_Z1, FIJO, PED_CUT, box, cbox, rbox, cyl,
                    cyl_c, fuse, cut, superellipse_wire, loft)
import body
import core
import refs

ARM_HOLE_R = 13.3
TUMMY_R = 25.2
CLIP_W = 14.0


def _surface_point(ang_deg, z, offset):
    a, b, n = body.profile_at(z, offset)
    t = math.radians(ang_deg)
    c, s = math.cos(t), math.sin(t)
    return a * math.copysign(abs(c) ** (2 / n), c), b * math.copysign(abs(s) ** (2 / n), s)


def c_clip(x, y, z_center, slot_h, height=11.0, depth=7.0):
    """C-clip block on the shell's inner wall at (x, y) catching a horizontal plate edge."""
    t = math.degrees(math.atan2(y, x))
    blk = cbox(-depth / 2, 0, 0, depth, CLIP_W, height)
    slot = cbox(-depth / 2 - 0.5, 0, 0, depth - 0.8, CLIP_W + 2, slot_h)
    clip = blk.cut(slot)
    clip = clip.rotate(V(0, 0, 0), V(0, 0, 1), t)
    # push slightly into the wall so it fuses
    r = math.hypot(x, y)
    ux, uy = x / r, y / r
    return clip.translate(V(x + ux * 1.0, y + uy * 1.0, z_center))


def _deck_clip(ang):
    x, y = _surface_point(ang, DECK_Z0 + 1.5, BODY_WALL)
    return c_clip(x, y, (DECK_Z0 + DECK_Z1) / 2, core.DECK_T + 0.4)


def _beam_clip(x_at, y_sign):
    z = (core.BEAM_Z[0] + core.BEAM_Z[1]) / 2
    a, b, n = body.profile_at(z, BODY_WALL)
    # beam edge position along y for this x (beam is clipped to y in [SPINE_Y0, PLATE_Y1])
    y_edge = core.SPINE_Y0 if y_sign < 0 else core.PLATE_Y[1]
    blk = box(x_at - 7, x_at + 7, y_edge - 7.0 if y_sign < 0 else y_edge - 1.0,
              y_edge + 1.0 if y_sign < 0 else y_edge + 7.0, z - 6.0, z + 6.0)
    slot = box(x_at - 9, x_at + 9, y_edge - 0.6 if y_sign < 0 else y_edge - 2.0,
               y_edge + 2.0 if y_sign < 0 else y_edge + 0.6, core.BEAM_Z[0] - 0.2, core.BEAM_Z[1] + 0.2)
    # the shell supplies the outer part: bridge from the clip to the shell wall along y
    yw = -b * (1 - (abs(x_at) / a) ** n) ** (1 / n) if y_sign < 0 else b * (1 - (abs(x_at) / a) ** n) ** (1 / n)
    arm = box(x_at - 4, x_at + 4, min(yw, y_edge), max(yw, y_edge), z + 2.4, z + 6.0)
    return blk.cut(slot).fuse(arm)


def _split(sh, side):
    if side == "front":
        return sh.intersect(box(-200, 200, -200, ARM_AXIS_Y, -10, 400))
    return sh.intersect(box(-200, 200, ARM_AXIS_Y, 200, -10, 400))


def mic_points():
    m1, m2 = refs.respeaker_mics()
    pitch = (m2.x - m1.x) / 7
    xs = [m1.x + k * pitch for k in range(-5, 8)]
    return [(x, m1.z) for x in xs], (m1, m2)


def shell(side):
    sh = body.shell_solid()
    sh = _split(sh, side)
    # re-cut the bottom rim with a plane: gives a clean, watertight edge for slicing. The fixed variant has
    # no ball: the body ends flat just under the belly grille and stands on the pedestal.
    sh = sh.cut(box(-200, 200, -200, 200, -10, PED_CUT if FIJO else body.Z_HOLE + 0.6))
    inner = body.inner_solid()
    # arm hub holes (split by the seam)
    for sx in (-1, 1):
        sh = sh.cut(cyl_c(ARM_HOLE_R, 40, (sx * 72.0, ARM_AXIS_Y, ARM_AXIS_Z), (1, 0, 0)))
    if side == "front":
        # tummy grille opening (speaker), USB-C service port (Black Pill), microphone dots
        sh = sh.cut(cyl(TUMMY_R, 40, (0, -40, refs.SPEAKER_C[2]), (0, -1, 0)))
        (pts, _) = mic_points()
        for x, z in pts:
            sh = sh.cut(cyl(1.3, 30, (x, -50, z), (0, -1, 0)))
        bp = refs.board_to_world(99.0, 81.0, 11.8)
        sh = sh.cut(rbox(80.0, bp.y, bp.z, 40.0, 13.0, 8.4, 3.9, "X"))
        clips = [_deck_clip(a) for a in core.CLIP_ANGLES["front"]]
    else:
        # back vents: two columns over the Pi + one row near the power modules
        for x in (-17.0, 17.0):
            for k in range(5):
                z = 108.0 + 7.5 * k
                sh = sh.cut(rbox(x, 60.0, z, 24.0, 30.0, 3.6, 1.79, "Y"))
        for k in range(3):
            sh = sh.cut(rbox(0.0, 60.0, 166.0 + 7.5 * k, 34.0, 30.0, 3.6, 1.79, "Y"))
        clips = [_deck_clip(a) for a in core.CLIP_ANGLES["back"]]
    for c in clips:
        sh = sh.fuse(c.intersect(_split(body.outer_solid(), side)))
    # no alignment lip: nothing may cross the seam, so each shell prints flat on it (the C-clips on the
    # deck rim and the shoulder beam locate both halves)
    if False:
        lip_out = _inner_offset_solid(0.2)
        lip = lip_out.intersect(box(-200, 200, ARM_AXIS_Y - 3.5, ARM_AXIS_Y + 0.5, 104.0, 160.0))
        lip = lip.cut(_inner_offset_solid(1.7))
        # bridge the lip to the back shell's own wall (y >= seam)
        lip = lip.fuse(_inner_offset_solid(0.0).intersect(
            box(-200, 200, ARM_AXIS_Y, ARM_AXIS_Y + 0.5, 104.0, 160.0)).cut(_inner_offset_solid(1.7)))
        sh = sh.fuse(lip)
    return sh


_off_cache = {}


def _inner_offset_solid(extra):
    if extra not in _off_cache:
        secs = body.sections(BODY_WALL + extra)
        _off_cache[extra] = loft(secs)
    return _off_cache[extra]


def tummy_grille():
    """Orange speaker grille: follows the belly curve; a pocket on its back holds the 35 x 25 x 5.5 speaker
    (landscape), its front face on a thin stop rim. 2-3 dots of hot glue at the pocket corners."""
    cz = refs.SPEAKER_C[2]
    sp = refs.SPK
    disc = cyl(TUMMY_R - 0.25, 40, (0, -40, cz), (0, -1, 0))
    cap = body.outer_solid().intersect(disc).cut(body.inner_solid())
    yf = refs.SPEAKER_C[1] - sp["t"] / 2                 # speaker front face
    pw, ph = sp["w"] + 0.6, sp["h"] + 0.6                 # pocket (0.3 mm play per side)
    fw, fh = pw + 3.2, ph + 3.2                           # frame outline (1.6 mm walls)
    frame = box(-fw / 2, fw / 2, -80.0, yf + sp["t"] - 1.0, cz - fh / 2, cz + fh / 2)
    frame = frame.cut(box(-pw / 2, pw / 2, yf, 0.0, cz - ph / 2, cz + ph / 2))                 # pocket
    frame = frame.cut(box(-pw / 2 + 2.0, pw / 2 - 2.0, -90.0, 0.0, cz - ph / 2 + 2.0, cz + ph / 2 - 2.0))  # sound
    frame = frame.intersect(_inner_offset_solid(0.0))
    lip_disc = cyl(TUMMY_R + 2.4, 40, (0, -40, cz), (0, -1, 0)).cut(cyl(22.0, 50, (0, -30, cz), (0, -1, 0)))
    lip = _inner_offset_solid(0.2).intersect(lip_disc).cut(_inner_offset_solid(1.8))
    filler = _inner_offset_solid(0.0).intersect(disc).cut(_inner_offset_solid(0.2))
    g = fuse(cap, filler, frame, lip)
    g = g.cut(box(-60, 60, yf + sp["t"] - 1.0, 0, 0, 300))  # flat print face: nothing behind the frame back
    for k, w in zip(range(-2, 3), (22, 32, 36, 32, 22)):
        g = g.cut(rbox(0, -60, cz + 6.8 * k, w, 40, 3.4, 1.69, "Y").intersect(box(-60, 60, -90, yf - 1.2, 0, 300)))
    return g.clean()


def usb_plug():
    """Small orange plug for the Black Pill USB-C service port."""
    bp = refs.board_to_world(99.0, 81.0, 11.8)
    outer = body.outer_solid()
    slab = rbox(80.0, bp.y, bp.z, 40.0, 12.6, 8.0, 3.7, "X")
    cap = outer.intersect(slab).cut(body.inner_solid())
    a, b, n = body.profile_at(bp.z, 0)
    # cap thickness + a short friction plug
    plug = rbox(0, bp.y, bp.z, 6.0, 12.0, 7.4, 3.4, "X")
    x_wall = _x_at(bp.y, bp.z, BODY_WALL)
    plug = plug.translate(V(x_wall - 2.5, 0, 0))
    knob = cyl_c(2.2, 3.0, (_x_at(bp.y, bp.z, 0) + 1.2, bp.y, bp.z), (1, 0, 0))
    return fuse(cap, plug, knob).clean()


def _x_at(y, z, offset):
    a, b, n = body.profile_at(z, offset)
    return a * (1 - (abs(y) / b) ** n) ** (1 / n)
