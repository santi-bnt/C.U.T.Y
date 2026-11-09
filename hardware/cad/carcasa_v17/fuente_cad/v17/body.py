"""Body shell surfaces: a chubby superellipse 'bean' with a spherical bottom
concentric with the gimbal centre C (so it rolls inside the base dish with a constant gap)."""
from __future__ import annotations

import math

import cadquery as cq

from common import (V, CZ, RS, BODY_WALL, BALL_HOLE_R, superellipse_wire, loft, box, cyl)

# (z, a, b, n) outer profile above the ball; below C the section is the sphere RS.
UPPER = [
    (86.0, 60.0, 60.0, 2.0),
    (94.0, 63.6, 63.0, 2.14),
    (104.0, 68.8, 67.4, 2.40),
    (118.0, 72.4, 68.2, 2.52),
    (134.0, 73.6, 68.6, 2.62),
    (150.0, 73.0, 67.8, 2.64),
    (166.0, 71.4, 66.0, 2.62),
    (180.0, 70.4, 63.8, 2.60),
    (192.0, 66.6, 59.4, 2.52),
    (200.0, 57.6, 52.2, 2.36),
    (205.5, 46.0, 42.6, 2.18),
    (209.0, 34.0, 33.0, 2.0),
]
BODY_TOP = UPPER[-1][0]
Z_HOLE = CZ - math.sqrt(RS ** 2 - BALL_HOLE_R ** 2)


def sections(offset=0.0, npts=72):
    secs = []
    # spherical part, from the hole edge up to C
    zs = [Z_HOLE + (CZ - Z_HOLE) * k / 8 for k in range(8)]
    for z in zs:
        r = math.sqrt(max(RS ** 2 - (z - CZ) ** 2, 1.0)) - offset
        secs.append(superellipse_wire(r, r, 2.0, z, npts))
    for z, a, b, n in UPPER:
        secs.append(superellipse_wire(a - offset, b - offset, n, z, npts))
    return secs


def profile_at(z, offset=0.0):
    """Interpolated (a, b, n) of the outer surface at height z (linear between sections)."""
    if z <= CZ:
        r = math.sqrt(max(RS ** 2 - (z - CZ) ** 2, 0.0)) - offset
        return r, r, 2.0
    for (z0, a0, b0, n0), (z1, a1, b1, n1) in zip(UPPER, UPPER[1:]):
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0)
            return a0 + (a1 - a0) * t - offset, b0 + (b1 - b0) * t - offset, n0 + (n1 - n0) * t
    z, a, b, n = UPPER[-1]
    return a - offset, b - offset, n


def inside(x, y, z, offset):
    a, b, n = profile_at(z, offset)
    return (abs(x) / a) ** n + (abs(y) / b) ** n <= 1.0


_cache = {}


def outer_solid():
    if "o" not in _cache:
        _cache["o"] = loft(sections(0.0))
    return _cache["o"]


def inner_solid():
    if "i" not in _cache:
        # extend the inner loft slightly past both open ends so the shell is cleanly open
        secs = sections(BODY_WALL)
        _cache["i"] = loft(secs)
    return _cache["i"]


def shell_solid():
    if "s" not in _cache:
        o = outer_solid()
        i = inner_solid()
        sh = o.cut(i)
        # open the bottom and top completely
        sh = sh.cut(cyl(BALL_HOLE_R - 0.01, 20, (0, 0, Z_HOLE - 10)))
        sh = sh.cut(cyl(UPPER[-1][1] - BODY_WALL, 20, (0, 0, BODY_TOP - 10)))
        _cache["s"] = sh.clean()
    return _cache["s"]
