# C.U.T.Y Audio

Responsibilities: microphone capture, speaker playback, audio-device selection, speech-processing boundaries, and cached thinking asides.

Working files: `microphone.py`, `speaker.py`, `devices.py`, and `thinking.py`. Existing timing, device behavior, and provider-native PCM rates are preserved.

Speaker startup negotiates mono/stereo and a supported hardware rate instead
of requiring direct ALSA `hw` devices to accept 24 kHz. Playback uses the
existing PyAV dependency for streaming resampling and duplicates mono into
both channels when stereo is required. Provider audio and lip-sync timing
remain at 24 kHz; no ALSA configuration, GPIO or overlays are changed.

Current live providers supply speech transcription and reply audio. `stt.py` and `tts.py` are placeholders for future standalone processing, not implementations. Spanish thinking clips currently use a separate Edge TTS voice.

Inputs: microphone PCM and provider/aside PCM. Outputs: streamed microphone data and speaker audio. Does not own LLM reasoning, camera detection, face rendering, or motor control. A future mouth animation may consume speaking state or amplitude, but no amplitude-to-mouth integration exists.
