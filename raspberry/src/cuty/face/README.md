# C.U.T.Y Face

Animated face for the 480 × 320 touchscreen: big sparkly eyes that blink,
wander and **follow the person through the camera**, cheeks, and a mouth that
**opens and closes with C.U.T.Y's voice**. It only produces pixels; it never
controls motors, servos, the IMU or the STM32.

```python
from cuty.face.renderer import Face

face = Face()                      # 480x320, 2x supersampled
face.set_expression("happy", 0.8)  # any Expression value
face.look_at(x=0.72, y=0.43)       # normalized target, 0.5 = straight ahead
face.set_mouth_open(0.6)           # live speech level 0..1
face.blink()
image = face.render()              # PIL RGB image
```

| File | Role |
| --- | --- |
| `animations.py` | Expression presets and blending, gaze spring, idle wandering, random/double blinks, breathing, speech smoothing → `FacePose` |
| `eyes.py`, `mouth.py` | Drawing (masks for lids, iris clipping, tongue) |
| `renderer.py` | `Face` facade and `FaceRenderer` composition |
| `framebuffer.py` | NumPy RGB565 conversion and changed-rows-only `mmap` writes for the SPI panel |
| `link.py` | UDP messages from the voice app (expression, mouth level, look, blink) |
| `expressions.py`, `expression_sink.py` | Validated expression events, state baseline controller, console/face-link sinks |

Each of the ten `Expression` values has a face. Intensity blends from
neutral. When a new person appears the eyes blink and "perk up". Without a
camera target the eyes look around on their own.

Lip sync lives in `cuty/audio/lipsync.py`: every chunk written to the speaker
is measured in 20 ms windows and placed on a playback timeline, so the level
sent ~30 times per second matches what is audible, not when the network
delivered it. The touchscreen launcher (`touchscreen/cuty_launcher.py`) runs
the face, the camera tracker and the UDP listener in its C.U.T.Y mode.
