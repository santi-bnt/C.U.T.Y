# Body control

# Three-joint motion control

The current mechanical design has a fixed base, pedestal and torso. Only three joints are active: HEAD_PAN, LEFT_ARM and RIGHT_ARM. The carrier retains five servo connectors; J7, J8 and J9 are assigned by the CAD design to those three joints, while J10 and J11 remain reserved. Electrical pin mapping, calibration, physical fit and motion safety remain unverified. No body PID, gimbal control or body stabilization is part of the active design. See [FreeRTOS motion control](freertos-motion-control.md).
