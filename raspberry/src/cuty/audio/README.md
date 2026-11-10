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

## Local music output

`cuty.music.protocol` defines a provider-neutral async contract. `cuty.music.local.LocalMusicProvider` scans an explicitly configured user library and decodes supported files through the existing PyAV dependency into the existing speaker interface. No download, streaming source, music license, or web audio extraction is included. The async player owns one task and supports pause/resume/stop/track navigation and a local digital volume setting.

In touchscreen hands-free mode, `ConversationService` parses Gemini input-transcription events deterministically before applying music actions. The existing half-duplex turn pauses the music before microphone capture and resumes afterward; this reduces self-trigger risk but is a pause, not amplitude ducking or acoustic echo cancellation. The face remains in its independent process and receives a calm happy expression while the player reports `MUSIC_PLAYING`; no beat detection is claimed.
