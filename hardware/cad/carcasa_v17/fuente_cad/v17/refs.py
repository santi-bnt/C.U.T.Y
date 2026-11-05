"""Purchased components as simplified solids placed in the world frame.

Functions return lists of (name, solid, rgb). Keep-out volumes (plugs, cable bends,
fan air) are returned by *_keepouts() and only used for clearance checks.
Dimensions come from datasheets/drawings; everything marked 'measure' should be
checked with calipers on the real part before the final print.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import cadquery as cq

from common import (V, box, cbox, cyl, cyl_c, fuse, place, ARM_AXIS_Y, ARM_AXIS_Z, SPINE_Y0, SPINE_Y1,
                    PCB_STANDOFF, PCB_Z0, CZ, DECK_Z1, HEAD_Z0)

HERE = Path(__file__).resolve().parent
PARTS = json.loads((HERE / "parts.json").read_text())

COL = {
    "pcb": (0.10, 0.36, 0.19), "pcb_dark": (0.07, 0.07, 0.08), "metal": (0.74, 0.76, 0.79),
    "servo": (0.09, 0.09, 0.10), "white": (0.93, 0.93, 0.91), "pi": (0.18, 0.50, 0.25),
    "blue": (0.10, 0.28, 0.62), "battery": (0.14, 0.20, 0.33), "yellow": (0.96, 0.77, 0.18),
    "lcd": (0.02, 0.03, 0.05), "green_term": (0.17, 0.52, 0.31), "cap": (0.10, 0.16, 0.32),
}

# ------------------------------------------------------------------ MG996R (measure)
# Local frame: output shaft on +Z through the origin, top face at z=0, case below,
# case length along +X (shaft 10.15 mm from the end at -X).
SERVO = dict(L=40.7, W=19.7, H=37.0, shaft_off=10.15, tab_z0=-11.5, tab_z1=-9.0,
             tab_len=54.7, hole_dx=49.0, hole_dy=10.0, spline_top=5.9, boss_r=6.5, boss_h=2.5)


def mg996r_local(holes=True):
    s = SERVO
    x0 = -s["shaft_off"]
    x1 = x0 + s["L"]
    cx = (x0 + x1) / 2
    body = box(x0, x1, -s["W"] / 2, s["W"] / 2, -s["H"], 0)
    tabs = box(cx - s["tab_len"] / 2, cx + s["tab_len"] / 2, -s["W"] / 2, s["W"] / 2, s["tab_z0"], s["tab_z1"])
    if holes:
        for hx in (cx - s["hole_dx"] / 2, cx + s["hole_dx"] / 2):
            for hy in (-s["hole_dy"] / 2, s["hole_dy"] / 2):
                tabs = tabs.cut(cyl(2.2, 4, (hx, hy, s["tab_z0"] - 1)))
    boss = cyl(s["boss_r"], s["boss_h"], (0, 0, 0))
    small = cyl(4.0, 1.5, (12.0, 0, 0))
    spline = cyl(2.95, s["spline_top"] - s["boss_h"], (0, 0, s["boss_h"]))
    cable = box(x0 - 3, x0, -3.5, 3.5, -s["H"] + 2, -s["H"] + 6)
    return fuse(body, tabs, boss, small, cable), spline


def servo_hole_positions():
    s = SERVO
    cx = -s["shaft_off"] + s["L"] / 2
    return [(cx + sx * s["hole_dx"] / 2, sy * s["hole_dy"] / 2) for sx in (-1, 1) for sy in (-1, 1)]


# name: (origin = shaft centre on the top face, xdir = case length direction, zdir = shaft direction)
ARM_SERVO_TOP_X = 63.0
GIMBAL_SERVO_Z = 3.0 + SERVO["W"] / 2           # lying on its side on the base floor
GS_L_TOP_Y, GS_R_TOP_Y = -23.0, -27.0           # staggered so the mounting tabs never touch
GS_SHAFT_X = 38.5                                # tab ends interleave with 2.4 mm clearance
HUB_TOP_Z = 212.5                              # neck hub top (body), head servo boss rests on it
HEAD_SERVO_TOP_Z = HUB_TOP_Z + SERVO["boss_h"]
SERVO_FRAMES = {
    "servo_arm_R": ((ARM_SERVO_TOP_X, ARM_AXIS_Y, ARM_AXIS_Z), (0, 0, -1), (1, 0, 0)),
    "servo_arm_L": ((-ARM_SERVO_TOP_X, ARM_AXIS_Y, ARM_AXIS_Z), (0, 0, -1), (-1, 0, 0)),
    "servo_gimbal_L": ((-GS_SHAFT_X, GS_L_TOP_Y, GIMBAL_SERVO_Z), (1, 0, 0), (0, 1, 0)),
    "servo_gimbal_R": ((GS_SHAFT_X, GS_R_TOP_Y, GIMBAL_SERVO_Z), (-1, 0, 0), (0, 1, 0)),
    "servo_head": ((0.0, 0.0, HEAD_SERVO_TOP_Z), (1, 0, 0), (0, 0, -1)),
}


def servo(name):
    o, x, z = SERVO_FRAMES[name]
    case, spline = mg996r_local()
    return [(f"{name}_case", place(case, o, x, z), COL["servo"]),
            (f"{name}_spline", place(spline, o, x, z), COL["white"])]


def servo_point(name, local):
    """World position of a point given in a servo's local frame."""
    o, x, z = SERVO_FRAMES[name]
    xv, zv = V(*x).normalized(), V(*z).normalized()
    yv = zv.cross(xv)
    return V(*o) + xv * local[0] + yv * local[1] + zv * local[2]


def servo_envelope(name, grow=0.4):
    o, x, z = SERVO_FRAMES[name]
    s = SERVO
    x0, x1 = -s["shaft_off"] - grow, -s["shaft_off"] + s["L"] + grow
    cx = (x0 + x1) / 2
    body = box(x0, x1, -s["W"] / 2 - grow, s["W"] / 2 + grow, -s["H"] - grow, grow)
    tabs = box(cx - s["tab_len"] / 2 - grow, cx + s["tab_len"] / 2 + grow, -s["W"] / 2 - grow, s["W"] / 2 + grow,
               s["tab_z0"] - grow, s["tab_z1"] + grow)
    boss = cyl(s["boss_r"] + grow, s["boss_h"] + 0.5, (0, 0, 0))
    return place(fuse(body, tabs, boss), o, x, z)


# ------------------------------------------------------------------ carrier PCB (this repo, v1.1)
PCB_W, PCB_H, PCB_T = 100.0, 92.0, 1.6
PCB_BACK_Y = SPINE_Y0 - PCB_STANDOFF
PCB_FRONT_Y = PCB_BACK_Y - PCB_T
HEIGHTS = {"R": 2.6, "C3": 6.0, "D1": 2.8, "D2": 5.6, "D3": 5.6, "D4": 5.6, "C1": 21.0, "C2": 21.0,
           "J7": 8.6, "J8": 8.6, "J9": 8.6, "J10": 8.6, "J11": 8.6, "JP1": 8.6, "J15": 8.6, "J14": 8.6,
           "U1": 8.6, "J12": 9.0, "J13": 9.0, "J2": 10.0, "J3": 10.0, "J4": 10.0, "J5": 10.0, "J6": 10.0,
           "F1": 9.6, "F2": 9.6, "J1": 8.4}
PCB_HOLES = [(3.5, 3.5), (96.5, 15.5), (3.5, 88.5), (40.8, 88.6)]
PCB_X_OFF = 3.0                            # board shifted right: room for the battery plug on J1


def board_to_world(bx, by, h=0.0):
    """Carrier coordinates (x right, y down from the top edge, h above the parts side) -> world."""
    return V(bx - PCB_W / 2 + PCB_X_OFF, PCB_FRONT_Y - h, PCB_Z0 + PCB_H - by)


def board_box(b, h0, h1):
    x0, y0, x1, y1 = b
    p0 = board_to_world(x0, y1, h1)
    p1 = board_to_world(x1, y0, h0)
    return box(min(p0.x, p1.x), max(p0.x, p1.x), min(p0.y, p1.y), max(p0.y, p1.y),
               min(p0.z, p1.z), max(p0.z, p1.z))


def carrier_pcb():
    out = []
    board = box(-PCB_W / 2 + PCB_X_OFF, PCB_W / 2 + PCB_X_OFF, PCB_FRONT_Y, PCB_BACK_Y, PCB_Z0, PCB_Z0 + PCB_H)
    for hx, hy in PCB_HOLES:
        p = board_to_world(hx, hy)
        board = board.cut(cyl_c(1.6, 4, (p.x, PCB_BACK_Y - PCB_T / 2, p.z), (0, 1, 0)))
    out.append(("pcb_board", board, COL["pcb"]))
    colors = {"C1": COL["cap"], "C2": COL["cap"], "J1": COL["yellow"], "D2": (0.2, 0.8, 0.3),
              "D3": (0.2, 0.4, 0.9), "D4": (0.9, 0.2, 0.2)}
    for r in ("J2", "J3", "J4", "J5", "J6"):
        colors[r] = COL["green_term"]
    for ref, p in PARTS.items():
        if ref.startswith("H") or ref == "NT1":
            continue
        key = ref if ref in HEIGHTS else ("R" if ref.startswith("R") else None)
        if key is None:
            continue
        b = p["box"]
        bb = (b[0] + 0.6, b[1] + 0.6, b[2] - 0.6, b[3] - 0.6)
        out.append((f"pcb_{ref}", board_box(bb, 0.0, HEIGHTS[key]), colors.get(ref, COL["pcb_dark"])))
    out.append(("pcb_blackpill", board_box((45.99, 70.61, 98.80, 91.39), 8.6, 10.2), COL["pcb_dark"]))
    out.append(("pcb_blackpill_usb", board_box((92.3, 77.4, 99.5, 84.6), 10.2, 13.4), COL["metal"]))
    out.append(("respeaker_hat", board_box((36.37, 22.27, 101.37, 52.27), 11.0, 12.6), COL["pcb_dark"]))
    out.append(("respeaker_jack", board_box((40.0, 24.3, 46.0, 29.3), 12.6, 17.6), COL["metal"]))
    for ref, col in (("F1", (0.85, 0.2, 0.18)), ("F2", (0.86, 0.76, 0.55))):
        b = PARTS[ref]["box"]
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        out.append((f"fuse_{ref}", board_box((cx - 5.4, cy - 1.9, cx + 5.4, cy + 1.9), 9.6, 17.6), col))
    return out


def respeaker_mics():
    """World positions of the two microphones (top face of the HAT, at its short ends)."""
    return [board_to_world(39.0, 37.3, 12.6), board_to_world(98.7, 37.3, 12.6)]


def carrier_keepouts():
    k = []
    k.append(("ko_servo_plugs", board_box((0.5, 49.5, 9.6, 83.5), 8.6, 26.0)))
    k.append(("ko_j12_plug", board_box((39.5, 56.0, 98.4, 65.5), 9.0, 19.0)))
    k.append(("ko_j13_plug", board_box((57.3, 1.7, 98.4, 11.2), 9.0, 15.5)))
    for ref in ("J2", "J3", "J4"):
        b = PARTS[ref]["box"]
        k.append((f"ko_wire_{ref}", board_box((b[0] + 1, -9.0, b[2] - 1, 1.0), 0.0, 10.0)))
    for ref in ("J5", "J6"):
        b = PARTS[ref]["box"]
        k.append((f"ko_wire_{ref}", board_box((-10.0, b[1] + 1, 1.0, b[3] - 1), 0.0, 10.0)))
    k.append(("ko_battery_plug_J1", board_box((-14.0, 7.5, 1.0, 23.5), 0.0, 9.0)))   # female XT60, wires bent 90° down
    k.append(("ko_blackpill_usb", board_box((99.5, 77.0, 104.0, 85.0), 9.6, 14.0)))
    return k


# ------------------------------------------------------------------ Raspberry Pi 5 (flat on the deck, back)
PI_STANDOFF = 5.0
PI_Z0 = DECK_Z1 + PI_STANDOFF                 # board underside
PI_GPIO_EDGE_Y = -8.5
PI_HOLES = [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]   # drawing frame: x 0..85, y 0 (USB-C edge)..56 (GPIO edge)


def pi_to_world(px, py, h=0.0):
    return V(42.5 - px, PI_GPIO_EDGE_Y + (56 - py), PI_Z0 + 1.6 + h)


def pi_box(x0, y0, x1, y1, h0, h1):
    a = pi_to_world(x0, y0, h0)
    b = pi_to_world(x1, y1, h1)
    return box(min(a.x, b.x), max(a.x, b.x), min(a.y, b.y), max(a.y, b.y), min(a.z, b.z), max(a.z, b.z))


def raspberry_pi5():
    out = []
    board = pi_box(0, 0, 85, 56, -1.6, 0)
    for hx, hy in PI_HOLES:
        p = pi_to_world(hx, hy, -0.8)
        board = board.cut(cyl_c(1.4, 4, (p.x, p.y, p.z)))
    out.append(("pi5_board", board, COL["pi"]))
    out.append(("pi5_usb_eth", pi_box(64, 2, 87, 54, 0, 16.0), COL["metal"]))
    out.append(("pi5_cooler", pi_box(21, 10, 60, 46, 0, 13.0), (0.55, 0.58, 0.62)))
    out.append(("pi5_gpio", pi_box(7.1, 50.0, 57.9, 55.0, 0, 8.6), COL["pcb_dark"]))
    out.append(("pi5_usbc", pi_box(7.6, -1.0, 14.8, 7.0, 0, 3.4), COL["metal"]))
    out.append(("pi5_hdmi", pi_box(22, -0.5, 43, 7.0, 0, 3.6), COL["metal"]))
    return out


def pi_keepouts():
    return [
        ("ko_pi_usbc_plug", pi_box(4.0, -9.0, 18.5, 1.0, -2.0, 12.0)),       # right-angle USB-C plug
        ("ko_pi_idc", pi_box(6.0, 49.0, 59.0, 56.0, 8.6, 20.0)),             # 40-way IDC plug
        ("ko_pi_fan_air", pi_box(21, 10, 60, 46, 13.0, 19.0)),
        ("ko_pi_sd", pi_box(-14.0, 22.0, 1.0, 36.0, -4.0, 0.0)),             # micro-SD card access
    ]


# ------------------------------------------------------------------ power modules (standing behind the arm servos)
BUCK = (26.5, 15.0, 51.5)                  # XL4015 5 A class (51x26x14) or Pololu D24V90F6, standing
REG = (26.5, 13.0, 46.0)                   # 5.1 V / 5 A USB-C PD buck module, standing
BUCK_C = (0.0, -1.5, 157.0)                # against the back of the spine, between the arm servos
REG_C = (0.0, 15.5, 154.0)                 # on the power rack, behind the buck


def power_modules():
    return [("buck_6v", cbox(*BUCK_C, *BUCK), COL["blue"]), ("reg_5v1_usbc", cbox(*REG_C, *REG), (0.13, 0.13, 0.15))]


def power_keepouts():
    bx, by, bz = BUCK_C
    rx, ry, rz = REG_C
    return [("ko_buck_terms", cbox(bx, by, bz + BUCK[2] / 2 + 5, BUCK[0], BUCK[1], 10)),
            ("ko_reg_terms", cbox(rx, ry, rz + REG[2] / 2 + 5, REG[0], REG[1], 10)),
            ("ko_reg_usbc", cbox(rx, ry, rz - REG[2] / 2 - 6, 14, 10, 12))]


# ------------------------------------------------------------------ speaker, IMU
SPEAKER_C = (0.0, -52.0, 114.0)            # Ø40 x 16 mm, firing forward through the tummy grille
SPEAKER_R = 20.0
IMU_C = (-38.0, -31.0, DECK_Z1 + 3.6)       # GY-521 flat on the deck, front-left (under the servo plugs)


def speaker():
    cx, cy, cz = SPEAKER_C
    front = cyl(SPEAKER_R, 4.5, (cx, cy - 6.0, cz), (0, 1, 0))
    magnet = cyl(11.5, 12.0, (cx, cy - 1.5, cz), (0, 1, 0))
    return [("speaker_40mm", fuse(front, magnet), (0.12, 0.12, 0.13))]


def imu():
    return [("imu_mpu6050", cbox(IMU_C[0], IMU_C[1], IMU_C[2], 21.0, 16.0, 3.2), (0.10, 0.35, 0.65))]


# ------------------------------------------------------------------ battery (3S 2200 mAh, measure)
BATT = (106.0, 35.0, 25.0)
BATT_C = (0.0, 43.5, 5.0 + 12.5)               # on the drawer tray (top z 4.8)


def battery():
    b = cbox(*BATT_C, BATT[0], BATT[1], BATT[2])
    b = cq.Workplane().add(b).edges("|X").fillet(3).val()
    # balance + main lead leave the end face and fold up through the drawer notch
    lead = box(BATT_C[0] - BATT[0] / 2 - 2.6, BATT_C[0] - BATT[0] / 2, BATT_C[1] - 10, BATT_C[1] - 2,
               BATT_C[2] - 4, BATT_C[2] + 16)
    return [("battery_3s_2200", b, COL["battery"]), ("battery_lead", lead, (0.8, 0.15, 0.12))]


# ------------------------------------------------------------------ switches (12 V / 20 A round rocker, Ø20 mm)
def switches(positions):
    out = []
    for name, (p, d) in positions.items():
        bez = cyl(12.0, 2.5, (p[0], p[1], p[2]), d)
        body = cyl(9.8, 26.0, (p[0] - d[0] * 26, p[1] - d[1] * 26, p[2] - d[2] * 26), d)
        out.append((name, fuse(bez, body), (0.1, 0.1, 0.1)))
    return out


# ------------------------------------------------------------------ display + camera (head)
LCD = dict(pcb_w=85.0, pcb_h=56.0, depth=14.0, touch_w=83.79, touch_h=54.86, touch_t=1.6,
           active_w=74.04, active_h=49.56, holes=(29.0, 24.5))
CAM = dict(w=25.0, h=24.0, t=1.0, lens=8.5, lens_h=5.5, holes=(21.0, 12.5), hole_off=9.5)
