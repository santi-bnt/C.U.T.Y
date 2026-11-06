"""Head: helmet front/back shells, dark visor holding the display and camera, head base
with the pan servo, orange ears and antenna that lock the two shells together."""
from __future__ import annotations

import math

import cadquery as cq

from common import (V, HEAD_W, HEAD_D, HEAD_H, HEAD_YC, HEAD_ZC, HEAD_Z0, box, cbox, rbox, cyl, cyl_c, fuse, cut,
                    rounded_block, place, sphere, text_solid, FONT_MED)
import refs

WALL = 2.4
R_VERT, R_REST = 40.0, 30.0
SPLIT_Y = HEAD_YC
FRONT_Y = HEAD_YC - HEAD_D / 2
VISOR = dict(w=116.0, h=88.0, r=30.0, z=274.0)
DISP_Z = 266.0
CAM_Z = 309.0
EAR_Z = 274.0
EAR_R = 23.0
NECK_R_IN, NECK_R_OUT = 26.0, 30.0
NECK_Z0 = 205.5
BASE_Z0 = HEAD_Z0 + WALL
BASE_T = 3.0
BASE_SCREWS = [(-40.0, -14.0), (40.0, -14.0), (-40.0, 22.0), (40.0, 22.0)]
FLANGE_GAP, FLANGE_T = 0.2, 1.6
VISOR_IN_Y = FRONT_Y + WALL + FLANGE_GAP + FLANGE_T             # back face of the visor (shell + flange)
TOUCH_FRONT_Y = VISOR_IN_Y + 0.35                                # visor shell + its backing flange
LCD_BACK_Y = TOUCH_FRONT_Y + refs.LCD["stack"]                   # display PCB back (measured stack 5.8)
BAR_Y0 = LCD_BACK_Y + 0.2                                        # front face of the clamp bars (display + camera)
# camera: its back face lines up with the display back so one bar plate clamps both
CAM_BOARD_FRONT_Y = BAR_Y0 - refs.CAM["t"]
LENS_FRONT_Y = CAM_BOARD_FRONT_Y - refs.CAM["lens_h"]             # pokes ~0.9 mm into the visor's inner pocket
CAM_TOP_Z = CAM_Z + refs.CAM["lens_top"]
CAM_BOT_Z = CAM_TOP_Z - refs.CAM["h"]
CAM_BAR_Z = CAM_TOP_Z - 3.0
CAM_BOSS_X = refs.CAM["w"] / 2 + 3.6


def outer():
    return rounded_block(HEAD_W, HEAD_D, HEAD_H, R_VERT, R_REST, (0, HEAD_YC, HEAD_ZC))


def inner(extra=0.0):
    t = WALL + extra
    return rounded_block(HEAD_W - 2 * t, HEAD_D - 2 * t, HEAD_H - 2 * t, R_VERT - t, R_REST - t, (0, HEAD_YC, HEAD_ZC))


def visor_prism(grow=0.0):
    v = VISOR
    p = rbox(0, FRONT_Y - 10, v["z"], v["w"] + 2 * grow, 60.0, v["h"] + 2 * grow, v["r"] + grow, "Y")
    return p.translate(V(0, 10 + 15, 0))


def _shell():
    return outer().cut(inner())


def display_ref():
    L = refs.LCD
    out = []
    lcd_t = L["stack"] - L["touch_t"] - L["pcb_t"]
    touch = rbox(0, TOUCH_FRONT_Y + L["touch_t"] / 2, DISP_Z, L["touch_w"], L["touch_t"], L["touch_h"], 2.0, "Y")
    glass = rbox(0, TOUCH_FRONT_Y + L["touch_t"] + lcd_t / 2, DISP_Z, L["pcb_w"], lcd_t, L["pcb_h"], 1.0, "Y")
    pcb = cbox(0, LCD_BACK_Y - L["pcb_t"] / 2, DISP_Z, L["pcb_w"], L["pcb_t"], L["pcb_h"])
    header = cbox(-18.9, LCD_BACK_Y + L["header_h"] / 2, DISP_Z + L["pcb_h"] / 2 - 3.5, 33.0, L["header_h"], 5.0)
    active = cbox(0, TOUCH_FRONT_Y - 0.01, DISP_Z, L["active_w"], 0.05, L["active_h"])
    out.append(("lcd_touch_panel", touch, (0.04, 0.05, 0.07)))
    out.append(("lcd_module", glass, (0.15, 0.15, 0.17)))
    out.append(("lcd_pcb", pcb, (0.10, 0.36, 0.19)))
    out.append(("lcd_header", header, (0.05, 0.05, 0.05)))
    return out


def display_keepout():
    """Female 2x13 header on the display back + the male Dupont housings plugged into it (14 mm + bend)."""
    L = refs.LCD
    return cbox(-18.9, LCD_BACK_Y + L["header_h"] + 8.0, DISP_Z + L["pcb_h"] / 2 - 3.5, 36.0, 16.0, 8.0)


def camera_ref():
    C_ = refs.CAM
    board = cbox(0, CAM_BOARD_FRONT_Y + C_["t"] / 2, (CAM_TOP_Z + CAM_BOT_Z) / 2, C_["w"], C_["t"], C_["h"])
    hold_d = C_["lens_h"] - 1.4
    holder = cbox(0, CAM_BOARD_FRONT_Y - hold_d / 2, CAM_Z, C_["lens"], hold_d, C_["lens"])
    lens = cyl(3.6, 1.4, (0, LENS_FRONT_Y + 1.4, CAM_Z), (0, -1, 0))
    return [("camera_board", board, (0.10, 0.36, 0.19)), ("camera_lens", fuse(holder, lens), (0.03, 0.03, 0.04))]


def camera_cradle():
    """Locating features on the visor back: 4 front pads, 2 side guides with feet, 2 bosses for the clamp bar.
    The board drops in from above; the bar presses its back. Works for any hole pattern."""
    C_ = refs.CAM
    w2 = C_["w"] / 2
    y0 = VISOR_IN_Y - 0.6
    parts = []
    for sx in (-1, 1):
        for z in (CAM_TOP_Z - 1.6, CAM_BOT_Z + 1.6):
            xa, xb = sx * (w2 - 2.8), sx * (w2 - 0.4)
            parts.append(box(min(xa, xb), max(xa, xb), y0, CAM_BOARD_FRONT_Y, z - 1.2, z + 1.2))
        xa, xb = sx * (w2 + 0.4), sx * (w2 + 2.0)
        parts.append(box(min(xa, xb), max(xa, xb), y0, CAM_BOARD_FRONT_Y + 1.0, CAM_BOT_Z - 1.2, CAM_TOP_Z - 6.0))
        xa, xb = sx * (w2 - 2.8), sx * (w2 + 2.0)
        parts.append(box(min(xa, xb), max(xa, xb), y0, CAM_BOARD_FRONT_Y + 1.0, CAM_BOT_Z - 1.2, CAM_BOT_Z - 0.3))
        parts.append(cyl(2.6, CAM_BOARD_FRONT_Y + 0.8 - y0, (sx * CAM_BOSS_X, CAM_BOARD_FRONT_Y + 0.8, CAM_BAR_Z),
                         (0, -1, 0)))
    c = fuse(*parts).intersect(inner())
    for sx in (-1, 1):
        c = c.cut(cyl(0.8, 6.5, (sx * CAM_BOSS_X, CAM_BOARD_FRONT_Y + 0.9, CAM_BAR_Z), (0, -1, 0)))
    return c


def camera_bar():
    """Clamp bar across the top of the camera's back, 2 x M2 x 10 into the cradle bosses."""
    bar = rbox(0, BAR_Y0 + 1.5, CAM_BAR_Z, 2 * CAM_BOSS_X + 6.0, 3.0, 5.6, 2.7, "Y")
    for sx in (-1, 1):
        bar = bar.cut(cyl_c(1.2, 10, (sx * CAM_BOSS_X, BAR_Y0 + 1.5, CAM_BAR_Z), (0, 1, 0)))
    return bar


# ------------------------------------------------------------------ shells
def _ear_hole():
    return [cyl_c(5.2, 30, (sx * HEAD_W / 2, HEAD_YC, EAR_Z), (1, 0, 0)) for sx in (-1, 1)]


def _ear_boss():
    out = []
    for sx in (-1, 1):
        b = cyl(10.0, 5.0, (sx * (HEAD_W / 2 - WALL), HEAD_YC, EAR_Z), (-sx, 0, 0))
        out.append(b)
    return out


def _antenna_hole():
    return cyl_c(4.2, 30, (0, HEAD_YC, HEAD_Z0 + HEAD_H), (0, 0, 1))


def _antenna_boss():
    return cyl(8.0, 5.0, (0, HEAD_YC, HEAD_Z0 + HEAD_H - WALL), (0, 0, -1))


def shell(side):
    sh = _shell()
    bosses = fuse(*_ear_boss(), _antenna_boss())
    sh = sh.fuse(bosses.intersect(inner(-0.01)))
    if side == "front":
        sh = sh.intersect(box(-200, 200, -200, SPLIT_Y, 0, 500))
        sh = sh.cut(visor_prism(0.0).intersect(box(-200, 200, -200, SPLIT_Y - 20, 0, 500)))
    else:
        sh = sh.intersect(box(-200, 200, SPLIT_Y, 200, 0, 500))
        # name plate debossed on the back of the helmet
        back_y = HEAD_YC + HEAD_D / 2
        sh = sh.cut(text_solid("C.U.T.Y", 17.0, (0, back_y - 1.0, 292.0), (-1, 0, 0), (0, 1, 0), 3.0))
    for h in _ear_hole():
        sh = sh.cut(h)
    sh = sh.cut(_antenna_hole())
    # neck opening + neck ring (rotates with the head, hides the hub)
    sh = sh.cut(cyl(NECK_R_IN, 20, (0, 0, HEAD_Z0 - 5)))
    ring = cyl(NECK_R_OUT, HEAD_Z0 - NECK_Z0 + WALL, (0, 0, NECK_Z0)).cut(cyl(NECK_R_IN, 30, (0, 0, NECK_Z0 - 5)))
    half = box(-200, 200, -200, SPLIT_Y, 0, 500) if side == "front" else box(-200, 200, SPLIT_Y, 200, 0, 500)
    sh = sh.fuse(ring.intersect(half))
    # base plate screws from below (2 per shell)
    for x, y in BASE_SCREWS:
        if (y < SPLIT_Y) == (side == "front"):
            sh = sh.cut(cyl(1.7, 10, (x, y, HEAD_Z0 - 1)))
            sh = sh.cut(cyl(3.0, 1.6, (x, y, HEAD_Z0 - 0.01)))
    # alignment pins (front) / holes (back) on the seam, inside the corners
    for (x, z) in ((-74.5, 300.0), (74.5, 300.0), (-74.5, 246.0), (74.5, 246.0)):
        blk = cbox(x, SPLIT_Y + (-3.0 if side == "front" else 3.0), z, 7.0, 6.0, 7.0)
        sh = sh.fuse(blk.intersect(inner(-0.01).fuse(_shell())))
        if side == "front":
            sh = sh.fuse(cyl(1.4, 3.5, (x, SPLIT_Y, z), (0, 1, 0)))
        else:
            sh = sh.cut(cyl(1.6, 4.0, (x, SPLIT_Y - 0.01, z), (0, 1, 0)))
    return sh.clean()


# ------------------------------------------------------------------ visor
def visor():
    """Dark visor: follows the helmet curve; display pocket + camera mount behind it."""
    shell_band = outer().cut(inner())
    v = shell_band.intersect(visor_prism(-0.25))
    # backing flange: 0.2 mm off the helmet's inner wall around the opening (printable slip fit)
    filler = inner().cut(inner(FLANGE_GAP)).intersect(visor_prism(-0.25))
    flange = inner(FLANGE_GAP).cut(inner(FLANGE_GAP + FLANGE_T)).intersect(visor_prism(2.6))
    v = fuse(v, filler, flange)
    L = refs.LCD
    # active-area window
    v = v.cut(rbox(0, FRONT_Y, DISP_Z, L["active_w"] + 1.6, 20, L["active_h"] + 1.6, 2.5, "Y"))
    # camera window: round hole in the front skin + square pocket behind (lens holder may poke in)
    v = v.cut(cyl_c(6.2, 20, (0, FRONT_Y, CAM_Z), (0, 1, 0)))
    v = v.cut(rbox(0, VISOR_IN_Y - 1.0, CAM_Z, 12.4, 2.8, 12.4, 1.0, "Y"))
    # display pocket walls (locate the touch panel) — short ribs around the module
    rz = L["pcb_h"] / 2 + 1.4
    rx = L["pcb_w"] / 2 + 1.4
    for (x, z, dx, dz) in ((-22.0, DISP_Z + rz, 16, 2.0), (22.0, DISP_Z + rz, 16, 2.0), (0, DISP_Z - rz, 60, 2.0),
                           (rx, DISP_Z, 2.0, 30), (-rx, DISP_Z, 2.0, 30)):
        rib = cbox(x, TOUCH_FRONT_Y + 2.6, z, dx, 6.8, dz)
        v = v.fuse(rib.cut(outer().cut(inner())).intersect(inner()))
    # bosses for the two display clamp bars (M2 x 10, self-tapping)
    for (x, z) in display_bar_bosses():
        b = cyl(3.0, 12.0, (x, BAR_Y0, z), (0, -1, 0))
        b = b.intersect(inner())
        v = v.fuse(b)
        v = v.cut(cyl(0.8, 8.5, (x, BAR_Y0 + 0.1, z), (0, -1, 0)))
    # camera cradle (pads, guides, bosses for the clamp bar)
    v = v.fuse(camera_cradle())
    v = v.cut(rbox(0, VISOR_IN_Y - 1.0, CAM_Z, 12.4, 2.8, 12.4, 1.0, "Y"))
    return v.clean()


def display_bar_bosses():
    L = refs.LCD
    zs = (DISP_Z + L["pcb_h"] / 2 + 4.0, DISP_Z - L["pcb_h"] / 2 - 4.0)
    return [(x, z) for x in (-39.5, 39.5) for z in zs]


def display_bars():
    L = refs.LCD
    y0 = BAR_Y0
    out = []
    for x in (-39.5, 39.5):
        bar = rbox(x, y0 + 1.5, DISP_Z, 6.0, 3.0, L["pcb_h"] + 8.0 + 6.0, 2.9, "Y")
        for (bx, bz) in display_bar_bosses():
            if abs(bx - x) < 1:
                bar = bar.cut(cyl_c(1.4, 10, (bx, y0 + 1.5, bz), (0, 1, 0)))
        out.append(bar)
    out.append(camera_bar())
    return fuse(*out)


# ------------------------------------------------------------------ head base (pan servo + shell screws)
def head_base():
    plate = rbox(0, 4.0, BASE_Z0 + BASE_T / 2, 96.0, 48.0, BASE_T, 9.0, "Z")
    s = refs.SERVO
    o, xd, zd = refs.SERVO_FRAMES["servo_head"]
    cutout = box(-s["shaft_off"] - 0.6, -s["shaft_off"] + s["L"] + 0.6, -s["W"] / 2 - 0.6, s["W"] / 2 + 0.6, -30, 30)
    plate = plate.cut(place(cutout, o, xd, zd))
    plate = plate.cut(box(-20, 20, -24, -9.5, BASE_Z0 - 1, BASE_Z0 + 10))       # ribbon + FFC slot
    pillars = []
    for (hx, hy) in refs.servo_hole_positions():
        p = refs.servo_point("servo_head", (hx, hy, s["tab_z1"]))
        pillars.append((p.x, p.y, p.z))
    # two pillars (one per tab end) spanning the tab width
    for xs in sorted({round(p[0], 2) for p in pillars}):
        zt = pillars[0][2]
        pil = box(xs - 3.0, xs + 3.0, -s["W"] / 2, s["W"] / 2, BASE_Z0 + BASE_T, zt)
        plate = plate.fuse(pil)
    for (px, py, pz) in pillars:
        plate = plate.cut(cyl(1.25, 10, (px, py, pz - 8)))      # head servo tabs, M3 x 10 self-tapping
    for x, y in BASE_SCREWS:
        plate = plate.fuse(cyl(3.6, 7.0, (x, y, BASE_Z0)))
        plate = plate.cut(cyl(1.25, 12, (x, y, BASE_Z0 - 1)))
    return plate.clean()


# ------------------------------------------------------------------ ears + antenna (orange; they lock the shells)
def ear(sx):
    c = cyl_c(EAR_R, 18, (sx * (HEAD_W / 2 + 1.0), HEAD_YC, EAR_Z), (1, 0, 0))
    e = c.cut(outer())
    e = e.intersect(box(-HEAD_W / 2 - 10.0, HEAD_W / 2 + 10.0, -200, 200, 0, 500))
    # cosmetic ring groove on the outer face
    face_x = sx * (HEAD_W / 2 + 10.0)
    e = e.cut(cyl_c(EAR_R - 5.0, 3.0, (face_x, HEAD_YC, EAR_Z), (1, 0, 0)).cut(cyl_c(EAR_R - 8.5, 4, (face_x, HEAD_YC, EAR_Z), (1, 0, 0))))
    try:
        e = cq.Workplane().add(e).edges(cq.selectors.NearestToPointSelector((face_x, HEAD_YC, EAR_Z + EAR_R))).fillet(3.0).val()
    except Exception:
        pass
    # snap peg through the head wall (split by the shell seam -> locks both halves)
    peg = cyl(5.0, 12.0, (sx * (HEAD_W / 2 + 0.5), HEAD_YC, EAR_Z), (-sx, 0, 0))
    barb = cyl(5.7, 1.6, (sx * (HEAD_W / 2 - WALL - 5.0 - 0.2), HEAD_YC, EAR_Z), (-sx, 0, 0))
    peg = fuse(peg, barb)
    peg = peg.cut(cbox(sx * (HEAD_W / 2 - 6.0), HEAD_YC, EAR_Z, 10.0, 12.0, 2.0))
    return fuse(e, peg)


def antenna():
    top = HEAD_Z0 + HEAD_H
    disc = cyl(9.0, 3.0, (0, HEAD_YC, top - 0.6))
    disc = disc.cut(outer())
    disc = fuse(disc, cyl(9.0, 1.0, (0, HEAD_YC, top)))
    stalk = cyl(2.6, 11.0, (0, HEAD_YC, top + 0.5))
    ball = sphere(7.5, (0, HEAD_YC, top + 17.5))
    peg = cyl(4.0, 9.0, (0, HEAD_YC, top), (0, 0, -1))
    barb = cyl(4.6, 1.4, (0, HEAD_YC, top - 7.6), (0, 0, -1))
    a = fuse(disc, stalk, ball, peg, barb)
    a = a.cut(cbox(0, HEAD_YC, top - 6.0, 1.8, 12.0, 8.0))
    return a.clean()
