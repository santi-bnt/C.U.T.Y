# Vision

Camera → face detector (YuNet, Haar fallback) → face tracker → normalized target (X/Y, confidence). See the [vision module](../raspberry/src/cuty/vision/README.md).

Working: Raspberry Pi camera or USB webcam capture, face detection, closest-person selection with stickiness, smoothing, lost-target handling and camera reconnection. The touchscreen face uses the target for the pupils. No vision PWM or direct servo access. Recognition/registration and head goals remain later work. Not yet validated with the robot's physical camera.
