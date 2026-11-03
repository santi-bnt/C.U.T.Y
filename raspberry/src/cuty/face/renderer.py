"""The ``Face`` facade: high-level inputs in, 480x320 pictures out.

    face = Face()
    face.set_expression("happy", 0.8)
    face.look_at(x=0.72, y=0.43)      # normalized camera target, 0.5 = centre
    face.set_mouth_open(0.6)          # live speech level 0..1
    image = face.render()             # PIL RGB image

The face only produces pixels; it never touches motors or the camera.
"""

from __future__ import annotations

import random
import time

from PIL import Image, ImageDraw

from cuty.face.animations import PRESETS, FaceAnimator, FacePose
from cuty.face.eyes import draw_eye
from cuty.face.mouth import draw_mouth

BACKGROUND = (12, 21, 35)
BLUSH = (255, 122, 162)

EXPRESSIONS = tuple(PRESETS)


def _mix(color: tuple[int, int, int], bg: tuple[int, int, int], alpha: float) -> tuple[int, int, int]:
    return tuple(round(b + (c - b) * alpha) for c, b in zip(color, bg))


class FaceRenderer:
    """Draws a :class:`FacePose`. Supersampling (``ssaa``) smooths the edges."""

    def __init__(self, width: int = 480, height: int = 320, ssaa: int = 2,
                 background: tuple[int, int, int] = BACKGROUND) -> None:
        if ssaa not in (1, 2, 3, 4):
            raise ValueError("ssaa must be 1, 2, 3 or 4")
        self.width, self.height, self.ssaa = width, height, ssaa
        self.background = background
        # The layout is designed for 480x320 and scaled to other sizes.
        self._scale = min(width / 480, height / 320)

    def render(self, pose: FacePose) -> Image.Image:
        s = self.ssaa * self._scale
        size = (self.width * self.ssaa, self.height * self.ssaa)
        canvas = Image.new("RGB", size, self.background)
        # Centre the 480x320 design inside the target size.
        ox = (self.width / self._scale - 480) / 2
        oy = (self.height / self._scale - 320) / 2
        self._draw_cheeks(canvas, pose, ox, oy, s)
        for side, cx in ((-1, 150), (1, 330)):
            draw_eye(canvas, ox + cx, oy + 138, side=side, pose=pose, bg=self.background, s=s)
        draw_mouth(canvas, ox + 240, oy + 248, pose=pose, bg=self.background, s=s)
        if self.ssaa > 1:
            canvas = canvas.reduce(self.ssaa)
        return canvas

    def _draw_cheeks(self, canvas: Image.Image, pose: FacePose, ox: float, oy: float, s: float) -> None:
        strength = pose.params["blush"]
        if strength < 0.03:
            return
        d = ImageDraw.Draw(canvas)
        color = _mix(BLUSH, self.background, min(0.8, 0.62 * strength))
        y = oy + 226 + pose.bob * 0.8 + pose.gaze_y * 4
        for cx in (100, 380):
            x = ox + cx + pose.gaze_x * 6
            d.ellipse(((x - 30) * s, (y - 12) * s, (x + 30) * s, (y + 12) * s), fill=color)


class Face:
    """Animated face with the planned ``set_expression/look_at/set_mouth_open`` API."""

    def __init__(self, width: int = 480, height: int = 320, ssaa: int = 2,
                 seed: int | None = None, clock=time.monotonic) -> None:
        self.animator = FaceAnimator(rng=random.Random(seed))
        self.renderer = FaceRenderer(width, height, ssaa)
        self._clock = clock
        self.pose: FacePose | None = None

    def set_expression(self, expression, intensity: float = 1.0) -> None:
        name = getattr(expression, "value", expression)
        self.animator.set_expression(str(name).lower(), intensity)

    def look_at(self, x: float, y: float) -> None:
        self.animator.look_at(x, y, self._clock())

    def clear_target(self) -> None:
        self.animator.clear_target(self._clock())

    def set_mouth_open(self, level: float) -> None:
        self.animator.set_speech(level, self._clock())

    def blink(self) -> None:
        self.animator.blink(self._clock())

    def render(self, now: float | None = None) -> Image.Image:
        self.pose = self.animator.update(self._clock() if now is None else now)
        return self.renderer.render(self.pose)
