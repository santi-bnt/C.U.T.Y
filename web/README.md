# C.U.T.Y Web

Future dashboard and 3D digital twin only. No frontend scaffold, server, package manager, or new dependency is introduced.

Planned views: robot online/offline; STM32 connection; Raspberry CPU/temp; battery; current expression; LLM local/cloud provider; camera status; face detected and X/Y; head pan/tilt; body roll/pitch; PID target/measured/error; servo positions; logs; 3D digital twin.

`dashboard/` is the future UI. `digital-twin/models/` holds derived visualization assets and `digital-twin/animations/` holds visualization animations. Native mechanical sources remain in CAD. Consume the future Raspberry telemetry boundary; never own PWM, IMU acquisition, or control loops.
