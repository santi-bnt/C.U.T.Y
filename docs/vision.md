# Vision

Camera → face detector (YuNet, Haar fallback) → face tracker → normalized target (X/Y, confidence). See the [vision module](../raspberry/src/cuty/vision/README.md).

Implemented: Raspberry Pi camera or USB webcam capture, face detection, closest-person selection with stickiness, smoothing, lost-target handling and camera reconnection. The touchscreen face uses the target for the pupils. Camera initialization has been observed on the Pi with an OV5647; successful physical face detection and gaze tracking still need confirmation. Vision produces no PWM and has no direct servo access. Identity recognition/registration and physical head movement through STM32F401 goals remain future work.
