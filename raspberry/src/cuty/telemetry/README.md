# C.U.T.Y Telemetry

Future aggregation/server boundary for Raspberry status, provider status, vision/expression status, and STM32 telemetry. `telemetry.py` contains only a TODO.

The web dashboard should consume this boundary rather than reading devices or sending PWM itself. Transport, authentication, update rates, storage, and command authority are undecided. No HTTP/WebSocket server or dependency is added.
