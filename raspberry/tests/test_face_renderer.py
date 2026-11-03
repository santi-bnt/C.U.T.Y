"""Animated face: rendering, gaze, blinking, mouth and framebuffer output."""

import numpy as np
import pytest

pytest.importorskip("PIL")

from cuty.face.animations import NEUTRAL, PRESETS, FaceAnimator, expression_target
from cuty.face.expressions import Expression
from cuty.face.framebuffer import FramebufferWriter, to_rgb565
from cuty.face.renderer import Face

IRIS = np.array([63, 211, 180])
SCLERA = np.array([244, 247, 255])


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def settle(face, clock, seconds=1.5, **each_frame):
    """Run the animation with blinking and idle wandering frozen."""
    face.animator._next_blink = face.animator._next_wander = 1e9
    image = None
    for _ in range(int(seconds * 30)):
        clock.now += 1 / 30
        if "look" in each_frame:
            face.look_at(*each_frame["look"])
        if "speech" in each_frame:
            face.set_mouth_open(each_frame["speech"])
        image = face.render()
    return np.asarray(image).astype(int)


def mask_of(pixels, color, tol=12):
    return (np.abs(pixels - color).sum(axis=2) < tol)


def new_face():
    clock = Clock()
    face = Face(seed=3, clock=clock)
    face.render()
    return face, clock


def test_every_expression_in_the_voice_app_has_a_face():
    assert {e.value for e in Expression} == set(PRESETS)
    for name in PRESETS:
        face, clock = new_face()
        face.set_expression(name, 0.8)
        pixels = settle(face, clock, 0.5)
        assert pixels.shape == (320, 480, 3)


def test_expression_intensity_scales_from_neutral():
    half = expression_target("happy", 0.5)
    assert half["mouth_curve"] == pytest.approx((NEUTRAL["mouth_curve"] + 1.0) / 2)
    assert expression_target("happy", 0.0) == NEUTRAL
    with pytest.raises(ValueError):
        expression_target("angry")


def test_eyes_follow_the_target_left_and_right():
    centroids = []
    for x in (0.1, 0.9):
        face, clock = new_face()
        pixels = settle(face, clock, look=(x, 0.5))
        _, cols = np.nonzero(mask_of(pixels[:, :240], IRIS))   # left eye only
        centroids.append(cols.mean())
    assert centroids[0] < centroids[1] - 25


def test_eyes_follow_the_target_up_and_down():
    rows_mean = []
    for y in (0.1, 0.9):
        face, clock = new_face()
        pixels = settle(face, clock, look=(0.5, y))
        rows, _ = np.nonzero(mask_of(pixels, IRIS))
        rows_mean.append(rows.mean())
    assert rows_mean[0] < rows_mean[1] - 15


def test_target_times_out_back_to_idle():
    face, clock = new_face()
    settle(face, clock, 0.3, look=(0.9, 0.5))
    assert face.animator.tracking
    settle(face, clock, 1.0)
    assert not face.animator.tracking


def test_blink_closes_the_eyes():
    face, clock = new_face()
    open_white = mask_of(settle(face, clock, 0.5), SCLERA).sum()
    face.blink()
    clock.now += 0.08
    closed = np.asarray(face.render()).astype(int)
    assert mask_of(closed, IRIS).sum() == 0
    assert mask_of(closed, SCLERA).sum() < open_white * 0.2


def test_new_person_triggers_a_blink_and_perk():
    face, clock = new_face()
    settle(face, clock, 0.3)
    face.look_at(0.5, 0.5)
    clock.now += 0.07
    face.render()
    assert face.pose.openness < 0.5
    assert face.pose.perk > 0


def test_mouth_opens_with_speech_and_closes_after():
    def mouth_dark_pixels(pixels):
        region = pixels[215:320, 170:310]
        return mask_of(region, np.array([92, 23, 48]), 20).sum()

    face, clock = new_face()
    closed = mouth_dark_pixels(settle(face, clock, 0.5))
    talking = mouth_dark_pixels(settle(face, clock, 0.3, speech=0.9))
    assert closed == 0 and talking > 500
    after = settle(face, clock, 0.8)  # no more levels: mouth falls shut
    assert face.pose.speech < 0.05
    assert mouth_dark_pixels(after) == 0


def test_animator_ignores_non_finite_input():
    animator = FaceAnimator()
    animator.look_at(float("nan"), 0.5, 0.0)
    animator.set_speech(float("inf"), 0.0)
    pose = animator.update(0.1)
    assert not animator.tracking and pose.speech == 0


def test_rgb565_packing_matches_launcher_format():
    from PIL import Image
    image = Image.new("RGB", (2, 1))
    image.putpixel((0, 0), (255, 0, 0))
    image.putpixel((1, 0), (0, 255, 0))
    assert to_rgb565(image).tobytes() == b"\x00\xf8\xe0\x07"


def test_framebuffer_writes_only_changed_rows(tmp_path):
    path = tmp_path / "fb"
    path.write_bytes(bytes(8 * 4 * 2))
    frame = np.zeros((4, 8), dtype="<u2")
    with FramebufferWriter(path, 8, 4) as fb:
        assert fb.write(frame) == (0, 4)
        assert fb.write(frame) is None
        frame[2, 5] = 0xFFFF
        assert fb.write(frame) == (2, 3)
        fb.invalidate()
        assert fb.write(frame) == (0, 4)
        with pytest.raises(ValueError):
            fb.write(np.zeros((3, 8), dtype="<u2"))
    data = np.frombuffer(path.read_bytes(), dtype="<u2").reshape(4, 8)
    assert data[2, 5] == 0xFFFF and data.sum() == 0xFFFF


@pytest.mark.parametrize("fps", [5, 10, 15, 20, 30, 60])
def test_eye_motion_is_stable_at_any_frame_rate(fps):
    """Regression: an explicit-Euler spring diverged at 20 fps on the Pi."""
    animator = FaceAnimator()
    for i in range(fps * 20):
        now = i / fps
        animator.look_at(0.5 + 0.45 * (1 if (i // fps) % 2 else -1), 0.5, now)
        pose = animator.update(now)
        assert -1 <= pose.gaze_x <= 1 and -1 <= pose.gaze_y <= 1
    assert abs(animator._gx.value) < 2


def test_eyes_reach_the_target_quickly():
    animator = FaceAnimator()
    for i in range(10):  # half a second at 20 fps
        animator.look_at(1.0, 0.5, i / 20)
        pose = animator.update(i / 20)
    assert pose.gaze_x > 0.9
