"""Cute mouth: a smile line at rest, an open "D"/"o" with a tongue when talking."""

from __future__ import annotations

import math

from PIL import Image, ImageDraw

LIP = (255, 159, 184)
INSIDE = (92, 23, 48)
TONGUE = (255, 111, 145)

HALF_W = 24      # logical half width at scale 1
MAX_OPEN = 38    # logical opening height at full speech


def mouth_opening(pose) -> float:
    """Combine the resting opening of an expression with the live speech level."""
    rest = pose.params["mouth_open"]
    return max(0.0, min(1.0, rest + pose.speech * (1.0 - rest * 0.5)))


def draw_mouth(canvas: Image.Image, cx: float, cy: float, *, pose, bg, s: int) -> None:
    p = pose.params
    cx += p["mouth_x"] + pose.gaze_x * 5
    cy += pose.bob * 0.6 + pose.gaze_y * 3
    curve = p["mouth_curve"]
    wave = p["mouth_wave"]
    round_ = p["mouth_round"]
    opening = mouth_opening(pose)
    w = HALF_W * p["mouth_w"] * (1.0 - 0.35 * round_ * min(1.0, opening * 4)) + 3 * opening
    steps = 24

    def middle(u: float) -> float:
        # Smile: the middle sits lower than the corners.
        return cy + curve * 9 * (1 - u * u) - curve * 4 + wave * 3.5 * math.sin(u * math.pi * 2)

    if opening < 0.04:
        pts = [((cx + u * w) * s, middle(u) * s) for u in (i / steps * 2 - 1 for i in range(steps + 1))]
        width = int(6 * s)
        ImageDraw.Draw(canvas).line(pts, fill=LIP, width=width, joint="curve")
        rad = width / 2
        d = ImageDraw.Draw(canvas)
        for x, y in (pts[0], pts[-1]):
            d.ellipse((x - rad, y - rad, x + rad, y + rad), fill=LIP)
        return

    height = MAX_OPEN * opening
    upper, lower = [], []
    for i in range(steps + 1):
        u = i / steps * 2 - 1
        bulge = math.sqrt(max(0.0, 1 - u * u))
        top = middle(u) - round_ * height * 0.45 * bulge - height * 0.08 * bulge
        bot = middle(u) + height * (1 - round_ * 0.45) * bulge
        upper.append((cx + u * w, top))
        lower.append((cx + u * w, bot))
    outline = upper + lower[::-1]

    xs = [x for x, _ in outline]
    ys = [y for _, y in outline]
    margin = 6
    left, top = int((min(xs) - margin) * s), int((min(ys) - margin) * s)
    right, bottom = int((max(xs) + margin) * s), int((max(ys) + margin) * s)
    lw, lh = right - left, bottom - top

    def L(pt: tuple[float, float]) -> tuple[float, float]:
        return pt[0] * s - left, pt[1] * s - top

    shape = [L(pt) for pt in outline]
    layer = Image.new("RGB", (lw, lh), INSIDE)
    d = ImageDraw.Draw(layer)
    if opening > 0.18:
        tw, th = w * 0.62, height * 0.5
        ty = max(ys) - th * 0.45
        d.ellipse((*L((cx - tw, ty - th)), *L((cx + tw, ty + th))), fill=TONGUE)
    mask = Image.new("L", (lw, lh), 0)
    ImageDraw.Draw(mask).polygon(shape, fill=255)
    canvas.paste(layer, (left, top), mask)
    ImageDraw.Draw(canvas).line([(x + left, y + top) for x, y in shape + shape[:1]],
                                fill=LIP, width=int(4 * s), joint="curve")
