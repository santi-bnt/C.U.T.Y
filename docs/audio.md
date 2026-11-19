# Audio Boundaries

Optional, disabled-by-default FIR prefiltering for incoming PCM16 is described in [Digital Signal Processing / FIR Filters](digital-signal-processing-fir.md). It runs between microphone chunks and the current provider send call; provider reply audio, music, device configuration and half-duplex behavior are unchanged. Recognition improvement has not been tested.

[Audio module](../raspberry/src/cuty/audio/README.md) preserves microphone/speaker/device logic and thinking asides. [Raspberry usage](../raspberry/README.md) preserves setup and diagnostics.

Current keyboard push-to-talk, native provider PCM rates, independent receive/playback, first-response timeout, tool continuation, session context, language instructions, and thinking-phrase interruption remain unchanged. Providers currently supply transcription and spoken answers; standalone STT/TTS modules are TODOs.

Only fixed Spanish thinking phrases go to Edge TTS. Provider replies are instructed to match the user's current language. The touchscreen starts Gemini hands-free mode with a spoken greeting, local energy/silence boundaries and a spoken return-to-menu command. The microphone is closed while replies play; wake-word, barge-in and local inference are not implemented. Audio also drives the animated mouth through the local face link.
