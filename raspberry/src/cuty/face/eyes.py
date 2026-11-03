"""Cute eyes: white sclera, big teal iris, sparkly highlights and soft lids.

Drawing happens on a supersampled canvas. Each eye is painted on a small
layer and pasted through a mask, so lids and blinking simply carve the mask
and the iris is always clipped to the eye shape.
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw

SCLERA = (244, 247, 255)
SCLERA_SHADE = (214, 224, 241)
IRIS_RIM = (24, 128, 118)
IRIS = (63, 211, 180)
IRIS_GLOW = (128, 240, 214)
PUPIL = (12, 21, 35)
SHINE = (255, 255, 255)

EYE_A = 62      # half width at scale 1, in logical pixels
EYE_B = 74      # half height
IRIS_R = 47


def _star(cx: float, cy: float, r: float) -> list[tuple[float, float]]:
    points = []
    for i in range(8):
        rad = r if i % 2 == 0 else r * 0.38
        ang = -math.pi / 2 + i * math.pi / 4
        points.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    return points


def draw_eye(canvas: Image.Image, cx: float, cy: float, *, side: int, pose, bg, s: int) -> None:
    """Draw one eye centred at logical (cx, cy). ``side`` is -1 left, +1 right."""
    p = pose.params
    asym = p["asym"]
    perk = 1.0 + 0.07 * pose.perk
    a = EYE_A * p["eye_w"] * perk * (1 - 0.06 * asym if side < 0 else 1 + 0.05 * asym)
    b = EYE_B * p["eye_h"] * perk * (1 - 0.12 * asym if side < 0 else 1 + 0.07 * asym)
    openness = pose.openness
    upper = p["upper"] + (0.3 * asym if side < 0 else 0.0)

    # Look direction also nudges the whole eye a little, like a head turn.
    cx += pose.gaze_x * 7
    cy += pose.gaze_y * 5 + pose.bob

    closed_line = openness < 0.22 or upper > 0.92
    if closed_line:
        _draw_closed(canvas, cx, cy + b * 0.25, a, s)
        return

    bh = b * openness
    ecy = cy + (b - bh) * 0.35          # lids meet a bit below the middle
    margin = 4
    left, top = int((cx - a - margin) * s), int((ecy - bh - margin) * s)
    right, bottom = int((cx + a + margin) * s), int((ecy + bh + margin) * s)
    w, h = right - left, bottom - top
    if w <= 0 or h <= 0:
        return

    def L(x: float, y: float) -> tuple[float, float]:  # logical -> layer pixels
        return x * s - left, y * s - top

    layer = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(layer)
    box = (*L(cx - a, ecy - bh), *L(cx + a, ecy + bh))
    d.ellipse(box, fill=SCLERA_SHADE)
    d.ellipse((*L(cx - a, ecy - bh + 9), *L(cx + a, ecy + bh + 9)), fill=SCLERA)

    eye_top = ecy - bh
    lid_box = None
    if upper > 0.01:
        edge = eye_top + upper * 2 * bh
        lr = b * 1.6
        lid_box = (cx - a * 3.2, edge - 2 * lr, cx + a * 3.2, edge)
        # Shade under the lid edge on the white only; the iris is drawn on top.
        d.ellipse((*L(lid_box[0], lid_box[1] + 8), *L(lid_box[2], lid_box[3] + 8)), fill=SCLERA_SHADE)

    # Iris position: the further the gaze, the closer to the rim.
    r = IRIS_R * p["iris"] * perk
    ix = cx + pose.gaze_x * (a - r * 0.62)
    iy = ecy + pose.gaze_y * (b - r * 0.55) * max(openness, 0.4) + b * 0.04
    d.ellipse((*L(ix - r, iy - r), *L(ix + r, iy + r)), fill=IRIS_RIM)
    ri = r * 0.86
    d.ellipse((*L(ix - ri, iy - ri), *L(ix + ri, iy + ri)), fill=IRIS)
    rg = r * 0.55
    gy = iy + r * 0.22
    d.ellipse((*L(ix - rg, gy - rg * 0.85), *L(ix + rg, gy + rg * 0.85)), fill=IRIS_GLOW)
    rp = r * (0.44 if p["eye_h"] < 1.12 else 0.36)
    d.ellipse((*L(ix - rp, iy - rp), *L(ix + rp, iy + rp)), fill=PUPIL)

    # Highlights: a big shine up-left and a small one down-right.
    sparkle = p["sparkle"]
    hx, hy, hr = ix - r * 0.36, iy - r * 0.38, r * 0.25
    if sparkle > 0.5:
        d.polygon([L(*pt) for pt in _star(hx, hy, hr * (1.5 + 0.3 * sparkle))], fill=SHINE)
        d.polygon([L(*pt) for pt in _star(ix + r * 0.4, iy + r * 0.32, hr * 0.85)], fill=SHINE)
    else:
        d.ellipse((*L(hx - hr, hy - hr), *L(hx + hr, hy + hr)), fill=SHINE)
        sr = r * 0.11
        sx, sy = ix + r * 0.36, iy + r * 0.32
        d.ellipse((*L(sx - sr, sy - sr), *L(sx + sr, sy + sr)), fill=SHINE)

    # Mask: eye shape minus lids. Lids are big ellipses so their edge curves
    # like a real eyelid; a shaded band just below the edge gives depth.
    mask = Image.new("L", (w, h), 0)
    m = ImageDraw.Draw(mask)
    m.ellipse(box, fill=255)
    if lid_box is not None:
        m.ellipse((*L(lid_box[0], lid_box[1]), *L(lid_box[2], lid_box[3])), fill=0)
    slant = p["slant"]
    if slant > 0.01:
        base = eye_top + upper * 2 * bh
        drop = slant * bh * 0.6
        # The outer corner droops for sadness; side -1 has its outer edge on the left.
        outer_x, inner_x = (cx - a - margin, cx + a + margin) if side < 0 else (cx + a + margin, cx - a - margin)
        lid = [L(outer_x, base + drop), L(inner_x, base - drop * 0.15),
               L(inner_x, eye_top - margin * 3), L(outer_x, eye_top - margin * 3)]
        m.polygon(lid, fill=0)
    lower = p["lower"]
    if lower > 0.01:
        rr = b * 1.1
        lcy = ecy + bh + rr - lower * b * 1.3
        m.ellipse((*L(cx - a * 1.55, lcy - rr), *L(cx + a * 1.55, lcy + rr)), fill=0)
    canvas.paste(layer, (left, top), mask)


def _draw_closed(canvas: Image.Image, cx: float, cy: float, a: float, s: int) -> None:
    """A soft upward-curving lash line, the cute closed-eye look."""
    d = ImageDraw.Draw(canvas)
    box = ((cx - a * 0.78) * s, (cy - a * 0.38) * s, (cx + a * 0.78) * s, (cy + a * 0.38) * s)
    width = int(7 * s)
    d.arc(box, 18, 162, fill=SCLERA, width=width)
    rad = width / 2
    mx, my = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    rx, ry = (box[2] - box[0]) / 2 - rad, (box[3] - box[1]) / 2 - rad
    for ang in (18, 162):
        x = mx + rx * math.cos(math.radians(ang))
        y = my + ry * math.sin(math.radians(ang))
        d.ellipse((x - rad, y - rad, x + rad, y + rad), fill=SCLERA)
