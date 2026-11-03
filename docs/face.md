# Face

Raspberry owns eyes, pupils, mouth, blink, expressions, speaking animation and visual eye tracking. See the [face module](../raspberry/src/cuty/face/README.md) and [vision module](../raspberry/src/cuty/vision/README.md).

Working: the touchscreen's C.U.T.Y mode shows the animated face at up to 20 fps, the eyes follow the nearest person seen by the camera (or look around when nobody is there), expressions from the voice app's state machine and `set_expression` tool appear on the face, and the mouth moves with the audio C.U.T.Y is playing. Voice and face are separate processes joined by a local UDP link (`CUTY_FACE_LINK` / `CUTY_FACE_LISTEN`, port 5005). The face consumes targets and speaking state and produces pixels, never motor commands.

Pending: validation on the physical screen and camera, lip-sync delay tuning for the real speaker (`CUTY_LIPSYNC_DELAY`), and head movement toward the person (STM32 work).
