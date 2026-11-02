# Face Plan

Raspberry owns eyes, pupils, mouth, blink, expressions, speaking animation, and visual eye tracking. See [module boundaries and future interface examples](../raspberry/src/cuty/face/README.md).

Current expression events and console logging are working; the separate [touchscreen menu/demo](../raspberry/touchscreen/README.md) now provides basic framebuffer face drawing and tap-to-blink. Integration with conversational expressions and speaking animation is not implemented. The face consumes targets/speaking state and produces pixels, never motor commands. Display selection, coordinate mapping, frame rate, visual style, and amplitude synchronization are TBD.
