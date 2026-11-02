# C.U.T.Y Vision

Future flow: Camera → Face Detector → Face Tracker → normalized X/Y target.

Responsibilities: capture, detection, temporal tracking, confidence and target validity. Example future data (no class is implemented):

```python
FaceTarget(x=0.72, y=0.43, confidence=0.96)
```

The face renderer may consume this target for pupils; the brain/behavior layer may consume it to generate high-level head goals through the hardware bridge.

Vision must not produce PWM, drive servos, implement body PID, or render the display. Target origin, axis direction, timestamps, lost-target behavior, and filtering remain design decisions. Detection/tracking and later registration/recognition are separate roadmap phases.
