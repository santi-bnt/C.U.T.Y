# C.U.T.Y Brain

Owns conversation orchestration, personality, session states, and future memory/high-level behavior.

Working: `conversation.py` routes microphone audio, provider events, search/expression tool results, and speaker output. `personality.py` contains language matching and conversational rules. `states.py` validates IDLE/LISTENING/THINKING/SPEAKING/ERROR.

`memory.py` is a TODO only. Session context currently belongs to the live provider session; persistent memory and behavior/head tracking are not implemented.

Consumes audio, provider events, and future normalized vision targets. Produces spoken replies, expressions, and eventually high-level hardware goals. Does not own PWM, real-time PID, camera detection, or screen rendering.
