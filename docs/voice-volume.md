# Voice and music volume

C.U.T.Y. applies software gain to assistant PCM output and to local music PCM
separately. Values are percentages from 0 to 100. This does not change the
microphone gain or ALSA mixer settings. The microphone, face renderer, and
camera paths are independent.

Voice settings:

- `CUTY_VOICE_VOLUME` sets the initial Gemini/TTS level (default `70`).
- `CUTY_VOLUME_STEP` sets the increment for “sube/baja el volumen” (default
  `10`, valid 1–100).
- `CUTY_MUSIC_VOLUME` sets the local music level (default `70`).

Commands mentioning `música/music/canción/song` target music. Commands
mentioning `voz/voice/habla/speak` target the assistant voice. A general volume
command targets music while it is playing or paused, and otherwise targets the
assistant voice. “Silencio/mute” and “activa el sonido/unmute” with no target
mute or restore both sources. Each source restores its own last nonzero level.
“Pon el volumen al N %” sets the selected target; “súbele/bájale N %” adjusts
it by that amount. All values clamp to 0–100.

The parser handles the user's transcription deterministically. The reply audio
is held until the command is applied, so the next spoken response uses the new
voice level. Music gain applies to subsequent PCM chunks while music is playing.
The remote speaker path also receives voice gain. No system mixer or hardware
amplifier setting is changed.

## Raspberry Pi check

After updating the checkout and restarting the existing launcher service, try
the commands in front of the robot and inspect the result:

```sh
sudo journalctl -u cuty-launcher.service -f --no-pager
```

Successful changes produce `[VOLUME] voice=NN%` or `[VOLUME] music=NN%`.
Test voice commands while no music is playing, then test music commands while a
local track is playing. Confirm the loudness actually changes at the speaker,
and verify that speech remains understandable at the chosen minimum. The
software gain is digital attenuation and cannot make output louder than the
unscaled signal or independently control an amplifier's physical limit.

To set initial values, add for example the following to the environment file
loaded by the launcher, then restart its service:

```sh
CUTY_VOICE_VOLUME=70
CUTY_MUSIC_VOLUME=70
CUTY_VOLUME_STEP=10
```

Validate on the physical Raspberry Pi that the speaker loudness changes, music
and speech volumes remain independent, mute restore works, and no clipping or
audio dropouts are introduced. Automated tests cover parsing, bounds, PCM gain,
mute restore, and applying a recognized command before buffered response
audio. They do not establish perceived loudness or amplifier behavior.
