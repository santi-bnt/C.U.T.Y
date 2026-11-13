# C.U.T.Y Vision

Camera → face detector → face tracker → normalized look target.

```python
FaceTarget(x=0.72, y=0.43, confidence=0.96, timestamp=...)
```

Coordinates are 0..1 in **screen space**: (0.5, 0.5) is straight ahead and
`x` grows toward the screen's right. The camera image is mirrored by default
so the eyes look *at* the person; set `CUTY_CAMERA_MIRROR=0` if they look the
opposite way on your mounting.

- `camera.py`: Raspberry Pi camera (Picamera2, Y plane of YUV420) or USB
  webcam (OpenCV), 320 × 240 grayscale, optional rotation.
- `face_detector.py`: YuNet (`models/`, MIT licence, ~5 ms per frame, reports
  eye positions) with a Haar cascade fallback for old OpenCV builds.
- `face_tracker.py`: background thread, ~12 detections/s, prefers the closest
  face but keeps following the same person, smooths jitter, forgets the
  target after 0.8 s without detections and reopens a lost camera every 5 s.

| Variable | Default | Meaning |
| --- | --- | --- |
| `CUTY_CAMERA` | `auto` | `auto`, `picamera`, `usb` or `off` |
| `CUTY_CAMERA_INDEX` | `0` | USB camera index |
| `CUTY_CAMERA_ROTATE` | `0` | 0, 90, 180 or 270 (clockwise) |
| `CUTY_CAMERA_MIRROR` | `1` | `0` if the eyes move the wrong way |
| `CUTY_FACE_DETECTOR` | `auto` | `yunet` or `haar` |
| `CUTY_TRACK_FPS` | `12` | detection rate |
| `CUTY_CAMERA_HIGH_RES_SNAPSHOT` | `0` | Optional PiCamera2 main=1296×972 + lores=320×240 dual stream; off pending Pi validation |

Head following is an optional layer over this same camera loop. It is disabled
by default and only supports an in-memory dry-run PAN simulation. See
[`docs/head-follow.md`](../../../../docs/head-follow.md) for parameters,
validation and the hardware blockers. No second camera, PWM, UART, or servo
output is introduced.

Vision never produces PWM, drives servos, implements body PID or renders the
display. The same target can later feed high-level head goals through the
hardware bridge. Optional voice-triggered vision and local face templates are
documented in [`docs/face-vision.md`](../../../../docs/face-vision.md). They
reuse this tracker and camera; they do not add another capture device. SFace
needs a separately installed OpenCV-contrib runtime and model, is disabled in
practice until configured, and has not been physically validated. Images are
not stored, and person embeddings stay on the Pi.

The optional dual-resolution snapshot mode and Pi benchmark procedure are
documented in [`docs/vision-performance.md`](../../../../docs/vision-performance.md).
Keep high-resolution mode disabled until OV5647 stream sizes, memory, latency,
voice, and face rendering have been measured together on the target Pi.
