"""Shared helpers and global dimensions for C.U.T.Y V17 "Nido".

World frame (mm): Z up from the desk, the robot looks toward -Y, X to the
viewer's right. C = gimbal centre (the body leans about it).
"""
from __future__ import annotations

import math

import cadquery as cq

V = cq.Vector

# ----------------------------------------------------------------- layout
C = (0.0, 0.0, 86.0)          # gimbal centre (U-joint)
CZ = C[2]
RS = 60.0                     # radius of the body's spherical bottom (concentric with C)
GAP_DISH = 3.5                # body ball <-> base dish gap
DISH_R = RS + GAP_DISH
BASE_R = 86.0                 # base outer radius (Ø172, fits the A1 mini 180 bed)
BASE_RIM_Z = 66.0             # top of the base cushion rim
BASE_WALL = 2.4
BODY_WALL = 2.6
BALL_HOLE_R = 46.0            # open bottom of the body ball (hidden inside the dish)
DISH_HOLE_R = 40.0            # dish opening for post, push-rods and cables
TILT_DESIGN_DEG = 18.0        # clearances are verified to this lean (firmware limit 15)

DECK_Z0 = 97.0                # core deck underside
DECK_T = 3.0
DECK_Z1 = DECK_Z0 + DECK_T
SPINE_Y0, SPINE_Y1 = -14.0, -10.0
PCB_STANDOFF = 6.0
PCB_Z0 = 101.0                # carrier PCB bottom edge (board vertical, parts facing -Y)
ARM_AXIS_Z = 176.0
ARM_AXIS_Y = 6.0              # arm servo shafts; also the front/back split plane of the body
HEAD_Z0 = 212.0               # head bottom
HEAD_W, HEAD_D, HEAD_H = 160.0, 112.0, 128.0
HEAD_YC = 4.0                 # head centre (y); pan axis is the world Z axis
HEAD_ZC = HEAD_Z0 + HEAD_H / 2

PRINT_BED = 180.0


FONT_BOLD = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
FONT_MED = "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf"


def text_solid(txt, size, origin, xdir, normal, depth, font=None):
    """Extruded text (centred on origin, extruded `depth` along `normal`)."""
    pl = cq.Plane(origin=origin, xDir=xdir, normal=normal)
    w = cq.Workplane(pl).text(txt, size, depth, combine=False, halign="center", valign="center",
                              fontPath=font or FONT_BOLD)
    return w.val()


def box(x0, x1, y0, y1, z0, z1) -> cq.Solid:
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cbox(cx, cy, cz, dx, dy, dz) -> cq.Solid:
    return box(cx - dx / 2, cx + dx / 2, cy - dy / 2, cy + dy / 2, cz - dz / 2, cz + dz / 2)


def rbox(cx, cy, cz, dx, dy, dz, r, axis="Z") -> cq.Solid:
    """Box rounded on the edges parallel to `axis` (all edges with axis='ALL')."""
    wp = cq.Workplane("XY").box(dx, dy, dz)
    if r > 0:
        wp = wp.edges() if axis == "ALL" else wp.edges(f"|{axis}")
        wp = wp.fillet(r)
    return wp.val().translate(V(cx, cy, cz))


def rounded_block(dx, dy, dz, r_vert, r_rest, center=(0, 0, 0)):
    wp = cq.Workplane("XY").box(dx, dy, dz)
    if r_vert > 0:
        wp = wp.edges("|Z").fillet(r_vert)
    if r_rest > 0:
        wp = wp.edges().fillet(r_rest)
    return wp.val().translate(V(*center))


def cyl(r, h, base=(0, 0, 0), d=(0, 0, 1)) -> cq.Solid:
    return cq.Solid.makeCylinder(r, h, V(*base), V(*d))


def cyl_c(r, h, center, d=(0, 0, 1)) -> cq.Solid:
    """Cylinder centred on `center` along direction d."""
    dv = V(*d).normalized()
    b = V(*center) - dv * (h / 2)
    return cq.Solid.makeCylinder(r, h, b, dv)


def sphere(r, center=(0, 0, 0)) -> cq.Solid:
    return cq.Solid.makeSphere(r, V(*center), angleDegrees1=-90, angleDegrees2=90)


def fuse(*shapes):
    shapes = [s for s in shapes if s is not None]
    out = shapes[0]
    if len(shapes) > 1:
        out = out.fuse(*shapes[1:])
    return out.clean()


def cut(base, *tools):
    tools = [t for t in tools if t is not None]
    if not tools:
        return base
    return base.cut(*tools).clean()


def superellipse_pts(a, b, n, z, npts=72, cx=0.0, cy=0.0):
    pts = []
    for i in range(npts):
        t = 2 * math.pi * i / npts
        c, s = math.cos(t), math.sin(t)
        x = a * math.copysign(abs(c) ** (2 / n), c)
        y = b * math.copysign(abs(s) ** (2 / n), s)
        pts.append(V(cx + x, cy + y, z))
    return pts


def superellipse_wire(a, b, n, z, npts=72, cx=0.0, cy=0.0) -> cq.Wire:
    pts = superellipse_pts(a, b, n, z, npts, cx, cy)
    edge = cq.Edge.makeSpline(pts, periodic=True)
    return cq.Wire.assembleEdges([edge])


def loft(sections, ruled=False) -> cq.Solid:
    return cq.Solid.makeLoft(sections, ruled)


def superellipse_prism(a, b, n, z0, z1, npts=72):
    w = superellipse_wire(a, b, n, z0, npts)
    f = cq.Face.makeFromWires(w)
    return cq.Solid.extrudeLinear(f, V(0, 0, z1 - z0))


def spline_25t(outer_r=3.10, root_r=2.60, teeth=25):
    """Female 25T spline profile for the MG996R output (V16 values, 0.15 mm radial play)."""
    pts = []
    pitch = 2 * math.pi / teeth
    for i in range(teeth):
        for frac, rad in ((0.0, outer_r), (0.5, root_r)):
            a = (i + frac) * pitch
            pts.append((rad * math.cos(a), rad * math.sin(a)))
    return pts


def orient(shape, d):
    """Rotate a shape built along +Z so that +Z points along d."""
    dv = V(*d).normalized()
    z = V(0, 0, 1)
    if (dv - z).Length < 1e-9:
        return shape
    if (dv + z).Length < 1e-9:
        return shape.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    ax = z.cross(dv)
    ang = math.degrees(math.acos(max(-1, min(1, z.dot(dv)))))
    return shape.rotate(V(0, 0, 0), ax, ang)


def spline_socket(depth, at, d=(0, 0, 1)):
    """Cutter for a 25T female spline of `depth`, starting at `at` going along d."""
    prof = cq.Workplane("XY").polyline(spline_25t()).close().extrude(depth).val()
    return orient(prof, d).translate(V(*at))


def bbox(shape):
    b = shape.BoundingBox()
    return (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)


def dims(shape):
    b = shape.BoundingBox()
    return (round(b.xlen, 2), round(b.ylen, 2), round(b.zlen, 2))


def place(shape, origin, xdir, zdir):
    """Map a shape from its local frame (X, Z) to world axes xdir/zdir at origin."""
    pl = cq.Plane(origin=V(*origin), xDir=V(*xdir), normal=V(*zdir))
    return shape.moved(cq.Location(pl))


def mirror_x(shape):
    return shape.mirror("YZ")
