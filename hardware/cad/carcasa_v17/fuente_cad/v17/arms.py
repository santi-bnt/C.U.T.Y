"""Stubby arms on the shoulder servos + orange mitten hands + screw caps."""
from __future__ import annotations

import cadquery as cq

from common import V, ARM_AXIS_Y, ARM_AXIS_Z, box, cbox, cyl, cyl_c, fuse, cut, spline_socket
import refs

ARM_X0 = 75.0           # inner face of the arm plate (clears the belly, max half-width 73.6)
ARM_T = 12.0
ARM_LEN = 80.0          # shaft axis to the hand centre
TOP_R = 15.0
HAND_R = 13.5
HUB_R = 12.0
CAP_R = 7.0
HAND_SEAM = 1.0         # arm/hand joint height above the hand centre


def _spline_x0():
    s = refs.SERVO
    return refs.ARM_SERVO_TOP_X + s["boss_h"] + 0.1


def arm(sx):
    """Arm for side sx (+1 right, -1 left). Built for the right side then mirrored."""
    x_s = _spline_x0()
    hub = cyl(HUB_R, ARM_X0 - x_s + 0.5, (x_s, ARM_AXIS_Y, ARM_AXIS_Z), (1, 0, 0))
    prof = (cq.Workplane("YZ", origin=(ARM_X0, 0, 0))
            .moveTo(ARM_AXIS_Y + TOP_R, ARM_AXIS_Z)
            .threePointArc((ARM_AXIS_Y, ARM_AXIS_Z + TOP_R), (ARM_AXIS_Y - TOP_R, ARM_AXIS_Z))
            .lineTo(ARM_AXIS_Y - HAND_R, ARM_AXIS_Z - ARM_LEN)
            .threePointArc((ARM_AXIS_Y, ARM_AXIS_Z - ARM_LEN - HAND_R), (ARM_AXIS_Y + HAND_R, ARM_AXIS_Z - ARM_LEN))
            .close().extrude(ARM_T))
    plate = prof.val()
    plate = cq.Workplane().add(plate).edges("not |X").fillet(4.5).val()
    a = fuse(hub, plate)
    a = a.cut(spline_socket(3.3, (x_s, ARM_AXIS_Y, ARM_AXIS_Z), (1, 0, 0)))
    a = a.cut(cyl(1.7, 40, (x_s, ARM_AXIS_Y, ARM_AXIS_Z), (1, 0, 0)))
    a = a.cut(cyl(CAP_R + 0.15, 4.0, (ARM_X0 + ARM_T - 4.0, ARM_AXIS_Y, ARM_AXIS_Z), (1, 0, 0)))   # cap pocket
    a = a.cut(cyl(3.2, 10.0, (ARM_X0 + ARM_T - 9.0, ARM_AXIS_Y, ARM_AXIS_Z), (1, 0, 0)))          # screw head
    # hand socket: the mitten slides over this stub
    zc = ARM_AXIS_Z - ARM_LEN
    a = a.cut(box(ARM_X0 - 1, ARM_X0 + ARM_T + 1, ARM_AXIS_Y - 30, ARM_AXIS_Y + 30, zc - 30, zc + HAND_SEAM))
    stub = box(ARM_X0 + ARM_T / 2 - 3.5, ARM_X0 + ARM_T / 2 + 3.5, ARM_AXIS_Y - 7.0, ARM_AXIS_Y + 7.0,
               zc - 9.0, zc + HAND_SEAM + 0.5)
    a = fuse(a, stub)
    return a if sx > 0 else a.mirror("YZ")


def hand(sx):
    """Orange mitten: press-fits on the arm stub."""
    zc = ARM_AXIS_Z - ARM_LEN
    xm = ARM_X0 + ARM_T / 2
    body = cyl_c(HAND_R + 1.6, ARM_T + 2.4, (xm, ARM_AXIS_Y, zc), (1, 0, 0))
    body = cq.Workplane().add(body).edges().fillet(4.5).val()
    body = body.cut(box(xm - 20, xm + 20, -100, 100, zc + HAND_SEAM - 0.2, zc + 60))
    thumb = cq.Workplane().add(cyl_c(5.2, ARM_T + 0.4, (xm, ARM_AXIS_Y - HAND_R - 0.5, zc - 4.6), (1, 0, 0))).edges().fillet(2.0).val()
    h = fuse(body, thumb)
    h = h.cut(box(xm - 20, xm + 20, -100, 100, zc + HAND_SEAM - 0.2, zc + 60))
    h = h.cut(box(xm - 3.65, xm + 3.65, ARM_AXIS_Y - 7.15, ARM_AXIS_Y + 7.15, zc - 9.2, zc + 10))
    return h if sx > 0 else h.mirror("YZ")


def cap(sx):
    c = cyl(CAP_R, 4.4, (ARM_X0 + ARM_T - 4.0, ARM_AXIS_Y, ARM_AXIS_Z), (1, 0, 0))
    c = cq.Workplane().add(c).faces(">X").edges().fillet(1.6).val()
    return c if sx > 0 else c.mirror("YZ")
