# C.U.T.Y Brain

Owns conversation orchestration, personality, session states, and future memory/high-level behavior.

Working: `conversation.py` routes microphone audio, provider events, search/expression tool results, and speaker output. `personality.py` contains language matching and conversational rules. `states.py` validates IDLE/LISTENING/THINKING/SPEAKING/ERROR.

`memory.py` is a TODO only. Session context currently belongs to the live provider session; persistent memory is not implemented. Motion behavior is handled separately by `hardware.motion_actions`; optional physical head tracking is described in [`docs/head-follow.md`](../../../../docs/head-follow.md).

Consumes audio and provider events. Produces spoken replies, expressions and validated high-level motion requests through `hardware.motion_actions`. Does not own PWM, real-time PID, camera detection, or screen rendering.
