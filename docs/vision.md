# Vision Plan

Camera → face detector → face tracker → normalized target (X/Y, confidence). See [vision contract sketch](../raspberry/src/cuty/vision/README.md).

The same target can feed pupil rendering and high-level head behavior independently. No vision PWM or direct servo access. Camera selection, frame orientation, detector, identity tracking, confidence thresholds, timestamps, and lost-target handling are open. Recognition/registration is later work, not a prerequisite for basic tracking. Nothing is implemented in this restructure.
