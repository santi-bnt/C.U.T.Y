# Vision performance diagnosis

## What is measured

The implementation logs measurements without opening another camera or audio
stream:

- `[VISION PERF] fps`, average capture call, YuNet/Haar inference and time from
  `capture_array` delivery to PAN update. The last value excludes any older
  frame already buffered inside libcamera.
- Snapshot request wait, local IPC round trip, face masking, JPEG encoding,
  compressed byte count, and dimensions.
- Gemini image request wall time. The Gen AI SDK exposes this as one awaited
  operation; upload, server queue/inference and response transfer cannot be
  separated reliably from this call. The log does not pretend to measure those
  as independent phases.
- `[AUDIO PERF]` time from first voice chunk to the end of playback and time
  spent writing chunks to the existing speaker.
- `[FACE PERF]` touchscreen face FPS, mean render/write time and frames taking
  longer than the target period.
- `scripts/vision_benchmark.py` samples CPU and RSS for matching C.U.T.Y.
  processes via `/proc`. It does not touch camera, GPIO, microphone or speaker.

Frame-to-PAN timing starts when a frame is returned to Python. It is not a
sensor-exposure-to-PAN measurement: libcamera's internal buffer age is not
available from the current `capture_array` path.

## Baseline run on the Raspberry Pi

Update/install using the existing deployment procedure, then restart the
launcher. Leave `CUTY_CAMERA_HIGH_RES_SNAPSHOT` unset or set to `0` for the
baseline. Enter C.U.T.Y.'s animated face view and keep it there during the run.

Terminal 1, capture detailed logs:

```sh
sudo journalctl -u cuty-launcher.service -f --no-pager | grep --line-buffered -E '\[VISION PERF\]|\[AUDIO PERF\]|\[FACE PERF\]|ProviderError|timeout|overflow|xrun'
```

Terminal 2, sample process CPU/RSS for five minutes:

```sh
cd /home/santi/C.U.T.Y/raspberry
.venv/bin/python scripts/vision_benchmark.py --duration 300 --interval 1 \
  --csv /tmp/cuty-vision-baseline.csv
```

During the same five minutes, exercise ordinary voice turns, one visual
question, speaker output and Music Mode if it is normally part of the workload.
Do not run another camera preview/capture program during the test. Repeat three
times after a 30-second warm-up. Compare median/p95 from journal samples and
the CSV, and inspect `vcgencmd get_throttled` and `vcgencmd measure_temp` before
and after each run. The script's summary is measured output, not a pass/fail
claim.

## Gemini timeout diagnosis

For a visual question, correlate these log entries by timestamp:

1. `capture_ipc_redact_encode_total_ms`, `ipc_roundtrip_decode_ms`, JPEG bytes
   and dimensions: local frame, masking/encoding and IPC costs.
2. `provider_request_start` and `provider_request_ms` (or `provider_request_timeout`):
   complete awaited Gemini request wall time.
3. `Primera voz en`, `[AUDIO PERF] response_playback_ms` and
   `speaker_write_ms`: time to first spoken audio and playback completion.

In the prior Pi log, local capture completed and the provider then hit its
45-second outer timeout. This confirms that the wait was in the one-shot
`generate_content` call, not the local capture path. It does not identify
whether the underlying cause was network delay, service queue/model latency,
or a transient API failure; the SDK's failed request exposed no more specific
cause in that log. The image was only a few kilobytes in the earlier IPC check,
so transfer size alone is not evidence for the timeout.

The app now gives the image request its own Gen AI client, separate from the
Live audio client, uses a 20-second default wall-clock budget, and logs the
actual request duration. This reduces the time C.U.T.Y. waits before fallback
and limits cancellation damage to the image client. The voice flow still needs
to finish the turn before another utterance can be processed; it is bounded,
not concurrent listening. If Live has gone stale by then, the local spoken
fallback reconnects the Live session once. This behavior needs validation on
the Pi/network.

## Optional high-resolution snapshot experiment

Picamera2 supports a `main` and a `lores` stream in one camera configuration and
can return arrays from both in one capture request. The optional code uses a
1296 × 972 YUV420 main stream and 320 × 240 YUV420 lores stream. YuNet continues
to use the lores luminance plane. It reads/copies main only for a user-requested
snapshot, but the camera/ISP still produces and buffers the configured main
stream continuously. This can increase CMA/buffer memory and camera bandwidth;
that cost is why the option is off by default.

The repository configuration alone is not proof that this stream combination
works with the OV5647 mode selected on the specific Pi OS/libcamera versions.
After recording the baseline, test only on the robot with a reversible systemd
override:

```sh
sudo systemctl edit cuty-launcher.service
```

Add:

```ini
[Service]
Environment=CUTY_CAMERA_HIGH_RES_SNAPSHOT=1
```

Then:

```sh
sudo systemctl daemon-reload
sudo systemctl restart cuty-launcher.service
sudo journalctl -u cuty-launcher.service -f --no-pager
```

Confirm startup reports the actual `main` and `lores` sizes, then repeat the
same workload and benchmark. Verify that ordinary tracking stays 320 × 240,
the requested JPEG has the larger dimensions, voice/TTS and face FPS remain
acceptable, and no camera timeout or audio overflow appears. If configuration
fails or resource/latency costs are unacceptable, remove the override with
`sudo systemctl revert cuty-launcher.service`, run `sudo systemctl daemon-reload`
and restart.

The image passed to Gemini still has detected face boxes masked in memory. A
missed face, profile, reflection or other biometric context can remain visible;
masking is not a guarantee of biometric anonymization. No image is saved by
this flow. Local SFace recognition and explicit enrollment consent remain
separate from the cloud scene-description request.

## Limits of the current measurements

- No Raspberry Pi benchmark was run as part of these code changes.
- FPS/latency logs report averages per five-second window; use external CSV or
  multiple runs for percentile analysis.
- The SDK does not expose distinct upload and inference timings for this call.
- CPU/RSS sampling is per matching process; it does not measure GPU/ISP load,
  total system memory, audio device underruns directly, or touchscreen frame
  presentation latency. Correlate logs with `vcgencmd` and audio errors.
- PAN remains simulated. The measured frame-to-PAN value is software path
  latency, not servo response time.
