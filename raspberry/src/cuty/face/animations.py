"""Time-based face animation: expression blending, gaze, blinking and mouth.

The animator never draws pixels. It turns high-level inputs (expression,
normalized look target, speech level) into a :class:`FacePose` that the
renderer can draw. All randomness goes through one ``random.Random`` so tests
can be deterministic.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field, replace

# Every numeric expression parameter, at its neutral value.
NEUTRAL: dict[str, float] = {
    "eye_w": 1.0,         # eye width scale
    "eye_h": 1.0,         # eye height scale
    "iris": 1.0,          # iris size scale
    "upper": 0.0,         # upper lid closure 0..1 (sleepy, sad)
    "slant": 0.0,         # +1 droops the outer corners (sad)
    "lower": 0.0,         # lower lid rise 0..1 (smiling eyes)
    "asym": 0.0,          # left eye squints, right eye widens (confused)
    "sparkle": 0.0,       # star-shaped highlights (excited)
    "blush": 0.55,        # cheek blush strength
    "gaze_x": 0.0,        # gaze bias added on top of tracking
    "gaze_y": 0.0,
    "track": 1.0,         # how much a camera target steers the gaze
    "mouth_curve": 0.6,   # +1 smile, -1 frown
    "mouth_w": 1.0,       # mouth width scale
    "mouth_open": 0.0,    # resting mouth opening (surprised, excited)
    "mouth_round": 0.0,   # morph toward an "o"
    "mouth_wave": 0.0,    # wavy mouth (confused)
    "mouth_x": 0.0,       # sideways mouth shift in pixels
}

# Full-intensity targets; missing keys stay neutral.
PRESETS: dict[str, dict[str, float]] = {
    "idle": {},
    "speaking": {"mouth_curve": 0.5},
    "listening": {"eye_w": 1.04, "eye_h": 1.08, "iris": 1.04, "mouth_curve": 0.35,
                  "mouth_round": 0.4, "mouth_w": 0.8, "blush": 0.7},
    "thinking": {"gaze_x": 0.55, "gaze_y": -0.65, "track": 0.25, "upper": 0.16,
                 "asym": 0.25, "mouth_curve": 0.05, "mouth_w": 0.7, "mouth_x": 14,
                 "mouth_wave": 0.25},
    "happy": {"lower": 0.42, "mouth_curve": 1.0, "mouth_w": 1.25, "blush": 1.0},
    "excited": {"eye_w": 1.08, "eye_h": 1.1, "sparkle": 1.0, "mouth_curve": 1.0,
                "mouth_w": 1.3, "mouth_open": 0.35, "blush": 1.0},
    "confused": {"asym": 0.75, "mouth_wave": 1.0, "mouth_curve": 0.0, "mouth_x": 8,
                 "gaze_x": -0.25, "gaze_y": -0.2, "track": 0.6},
    "sad": {"slant": 1.0, "upper": 0.22, "iris": 1.06, "mouth_curve": -0.8,
            "mouth_w": 0.85, "gaze_y": 0.35, "blush": 0.3, "track": 0.5},
    "sleepy": {"upper": 0.55, "mouth_curve": 0.2, "mouth_w": 0.6, "mouth_round": 0.6,
               "mouth_open": 0.1, "blush": 0.4, "track": 0.4},
    "surprised": {"eye_w": 1.12, "eye_h": 1.18, "iris": 0.82, "mouth_round": 1.0,
                  "mouth_open": 0.55, "mouth_w": 0.7, "mouth_curve": 0.0},
}


def expression_target(name: str, intensity: float = 1.0) -> dict[str, float]:
    """Neutral parameters pulled toward a preset by ``intensity`` (0..1)."""
    preset = PRESETS.get(name)
    if preset is None:
        raise ValueError(f"Unknown face expression: {name}")
    k = min(1.0, max(0.0, float(intensity)))
    return {key: base + (preset.get(key, base) - base) * k for key, base in NEUTRAL.items()}


@dataclass(frozen=True)
class FacePose:
    """Everything the renderer needs for one frame."""

    params: dict[str, float]
    gaze_x: float = 0.0       # -1 (screen left) .. +1 (screen right)
    gaze_y: float = 0.0       # -1 (up) .. +1 (down)
    openness: float = 1.0     # blink: 0 closed .. 1 open
    speech: float = 0.0       # 0 silent .. 1 loud
    bob: float = 0.0          # breathing offset in pixels
    perk: float = 0.0         # brief "I see you" widening, 0..1

    def with_params(self, **changes: float) -> FacePose:
        return replace(self, params={**self.params, **changes})


def _approach(current: float, target: float, dt: float, tau: float) -> float:
    if tau <= 0:
        return target
    return target + (current - target) * math.exp(-dt / tau)


@dataclass
class _Spring:
    """Critically damped spring for natural, overshoot-free eye motion."""

    value: float = 0.0
    velocity: float = 0.0

    def step(self, target: float, dt: float, omega: float) -> float:
        # Exact solution, so it stays stable at any frame rate (Euler steps
        # blow up once omega * dt approaches 1, i.e. ~20 fps for snappy eyes).
        x0 = self.value - target
        v0 = self.velocity
        decay = math.exp(-omega * dt)
        k = v0 + omega * x0
        self.value = target + (x0 + k * dt) * decay
        self.velocity = (v0 - omega * k * dt) * decay
        return self.value


@dataclass
class FaceAnimator:
    """Owns the face's moment-to-moment behaviour."""

    rng: random.Random = field(default_factory=random.Random)
    expression_tau: float = 0.14
    mouth_attack: float = 0.03
    mouth_release: float = 0.09
    speech_timeout: float = 0.3
    target_timeout: float = 0.6

    def __post_init__(self) -> None:
        self.expression = "idle"
        self.intensity = 1.0
        self._goal = expression_target("idle")
        self._params = dict(self._goal)
        self._gx, self._gy = _Spring(), _Spring()
        self._time: float | None = None
        # Look target from the camera (normalized 0..1, 0.5 is centre).
        self._target: tuple[float, float] | None = None
        self._target_at = -math.inf
        self._target_lost_at = -math.inf
        self._perk_until = -math.inf
        # Idle wandering when nobody is being tracked.
        self._wander = (0.0, 0.0)
        self._next_wander = 0.0
        # Blinking.
        self._blink_start = -math.inf
        self._double_blink_at: float | None = None
        self._next_blink = 0.0
        # Speech.
        self._speech_goal = 0.0
        self._speech_at = -math.inf
        self._speech = 0.0

    # ----- inputs ---------------------------------------------------------
    def set_expression(self, name: str, intensity: float = 1.0) -> None:
        self._goal = expression_target(name, intensity)
        self.expression, self.intensity = name, intensity

    def look_at(self, x: float, y: float, now: float) -> None:
        """Track a normalized target where (0.5, 0.5) is straight ahead."""
        if not (math.isfinite(x) and math.isfinite(y)):
            return
        if self._target is None and now - self._target_lost_at > 2.0:
            # Someone just showed up: a quick happy perk and blink.
            self._perk_until = now + 0.6
            self.blink(now)
        self._target = (min(1.0, max(0.0, x)), min(1.0, max(0.0, y)))
        self._target_at = now

    def clear_target(self, now: float) -> None:
        if self._target is not None:
            self._target_lost_at = now
        self._target = None

    def set_speech(self, level: float, now: float) -> None:
        if math.isfinite(level):
            self._speech_goal = min(1.0, max(0.0, level))
            self._speech_at = now

    def blink(self, now: float) -> None:
        if now - self._blink_start > 0.2:
            self._blink_start = now

    @property
    def tracking(self) -> bool:
        return self._target is not None

    # ----- per-frame update ----------------------------------------------
    def update(self, now: float) -> FacePose:
        dt = 1 / 30 if self._time is None else min(0.1, max(0.0, now - self._time))
        first = self._time is None
        self._time = now
        if first:
            self._next_blink = now + self.rng.uniform(1.0, 3.0)
            self._next_wander = now + self.rng.uniform(0.8, 2.0)

        for key, goal in self._goal.items():
            self._params[key] = _approach(self._params[key], goal, dt, self.expression_tau)
        p = self._params

        if self._target is not None and now - self._target_at > self.target_timeout:
            self.clear_target(now)

        # Gaze: camera target if present, else gentle wandering saccades.
        if self._target is not None:
            tx = (self._target[0] - 0.5) * 2.0
            ty = (self._target[1] - 0.5) * 2.0
            track = p["track"]
            want_x = tx * track + p["gaze_x"] * (1 - track * 0.6)
            want_y = ty * track + p["gaze_y"] * (1 - track * 0.6)
            omega = 22.0
        else:
            if now >= self._next_wander:
                if self.rng.random() < 0.35:
                    self._wander = (0.0, 0.0)
                else:
                    self._wander = (self.rng.uniform(-0.55, 0.55), self.rng.uniform(-0.35, 0.3))
                self._next_wander = now + self.rng.uniform(1.2, 3.8)
            want_x = self._wander[0] * 0.8 + p["gaze_x"]
            want_y = self._wander[1] * 0.8 + p["gaze_y"]
            omega = 16.0
        gx = max(-1.0, min(1.0, self._gx.step(max(-1.0, min(1.0, want_x)), dt, omega)))
        gy = max(-1.0, min(1.0, self._gy.step(max(-1.0, min(1.0, want_y)), dt, omega)))

        openness = self._blink_openness(now)

        # Speech: fast attack, slower release; fall silent if levels stop.
        goal = self._speech_goal if now - self._speech_at < self.speech_timeout else 0.0
        tau = self.mouth_attack if goal > self._speech else self.mouth_release
        self._speech = _approach(self._speech, goal, dt, tau)

        bob = math.sin(now * 2 * math.pi / 3.6) * 2.0
        perk = max(0.0, (self._perk_until - now) / 0.6) if now < self._perk_until else 0.0
        return FacePose(dict(p), gx, gy, openness, self._speech, bob, perk)

    def _blink_openness(self, now: float) -> float:
        if now >= self._next_blink and now - self._blink_start > 0.25:
            self._blink_start = now
            sleepy = self._params["upper"] > 0.4
            if self._double_blink_at is None and self.rng.random() < 0.15:
                self._double_blink_at = now + 0.32
            low, high = (1.5, 3.5) if sleepy else (2.5, 6.0)
            self._next_blink = now + self.rng.uniform(low, high)
        if self._double_blink_at is not None and now >= self._double_blink_at:
            self._blink_start = now
            self._double_blink_at = None
        t = now - self._blink_start
        close, hold, open_ = 0.06, 0.04, 0.10
        if t < 0:
            return 1.0
        if t < close:
            return 1.0 - t / close
        if t < close + hold:
            return 0.0
        if t < close + hold + open_:
            return (t - close - hold) / open_
        return 1.0
