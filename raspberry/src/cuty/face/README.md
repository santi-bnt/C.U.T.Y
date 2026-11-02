# C.U.T.Y Face

Responsibilities:
- eyes and pupils
- mouth
- blinking
- expressions
- speaking animations
- visual eye tracking

Does NOT control motors, servos, IMU, STM32, or camera detection.

Inputs: expression, normalized eye-target X/Y, speaking state, optional audio amplitude. Output: rendered facial display.

Working today: `expressions.py` contains validated expression events; `expression_sink.py` contains a console sink and state-based expression controller. These were moved intact from `src/cuty/robot`; they do not render a screen.

Future interface examples (not implemented):
```python
face.set_expression("happy")
face.look_at(x=0.72, y=0.43)
face.set_mouth_open(0.6)
```

`renderer.py`, `eyes.py`, `mouth.py`, and `animations.py` are TODO-only placeholders. Keep the existing expression controller API distinct from the planned visual facade.

## Existing touchscreen application

The real Raspberry framebuffer demo, touch menu and Wi-Fi panel are preserved in [touchscreen](../../../touchscreen/README.md). They are a standalone application, not an implementation of the future `face` facade above. They do not yet consume conversation expressions or speaking state. Keep the existing working UI intact until a separate runtime integration task.
