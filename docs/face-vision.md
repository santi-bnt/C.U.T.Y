# Voice-triggered vision and local face recognition

## What is implemented

- The touchscreen `FaceTracker` remains the only owner of the OV5647 camera. A voice request asks that loop for its next 320 × 240 frame; it does not open a second camera or retain a frame between requests.
- Color conversion is performed only for a requested snapshot. The existing grayscale YuNet/Haar detection and animated-eye tracking continue on the same capture loop.
- `Cuty, ¿qué estás viendo?` sends one in-memory JPEG to the configured Gemini image model. Detected face rectangles are covered before upload, and the prompt asks for a short description of visible objects without identities or personal traits. Images are not written to disk. The Gemini Live session speaks the result through the existing voice path.
- Face enrollment and matching are local SFace operations. Enrollment requires an explicit second spoken confirmation and collects five separate tracker frames by default. Only the user-provided name and embedding vectors are stored. No enrollment image is retained or sent to a provider.
- `¿Quién soy?` returns a name only when the local match passes both score and separation thresholds; otherwise it says it cannot recognize the face reliably. `Olvida mi rostro` asks for explicit confirmation and removes only the currently visible profile if it can be matched reliably. Other profiles are preserved.
- `FaceTracker` sends snapshots and recognition requests to the voice child over a private Unix socket under `/run`, mode `0600`, with Linux peer-UID verification. It is not an HTTP endpoint and is not reachable over the LAN.
- PAN head-follow remains a separate, disabled-by-default dry-run path. No GPIO, camera driver, display, ReSpeaker, STM32 or servo wiring has changed.

Voice intent recognition is deterministic over the existing Gemini input transcription. C.U.T.Y. does not gain a new wake-word engine: hands-free activation and turn boundaries remain those of the existing menu voice session. When no local SFace model is installed, identity commands fail closed and answer that local recognition is unavailable.

## Local setup on the Raspberry Pi

The repository does not include an SFace weight or personal face samples. Obtain the `face_recognition_sface_2021dec.onnx` model from the [OpenCV Zoo SFace model directory](https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface), review its current license and provenance, and put it in a private local model directory. The standard model is about 36.9 MB. `cv2.FaceRecognizerSF` requires an OpenCV build with the contrib face module; the Pi's existing OpenCV package may not include it. Check in the same Python environment used by the launcher:

```sh
cd /home/santi/C.U.T.Y/raspberry
source .venv/bin/activate
python -c 'import cv2; print(cv2.__version__, hasattr(cv2, "FaceRecognizerSF"))'
```

Do not replace a working system OpenCV or camera stack blindly. Install a compatible contrib build only after confirming it works with the installed Picamera2, NumPy and YuNet packages. The optional Python extra is available for environments where a compatible wheel is supported:

```sh
pip install -e '.[face-recognition]'
```

Set these variables in the launcher's protected systemd environment (the touchscreen parent owns the camera and the IPC socket):

```ini
Environment=CUTY_VISION_USER=santi
Environment=CUTY_SFACE_MODEL=/home/santi/.local/share/cuty/models/face_recognition_sface_2021dec.onnx
Environment=CUTY_FACE_PROFILE_PATH=/home/santi/.local/share/cuty/face_profiles.json
Environment=CUTY_FACE_MATCH_THRESHOLD=0.363
Environment=CUTY_FACE_MATCH_MARGIN=0.04
Environment=CUTY_FACE_MATCH_CALIBRATED=0
Environment=CUTY_FACE_ENROLL_SAMPLES=5
```

The voice child inherits the model and profile settings. Keep the profile directory private to the robot account and do not put the profile file in Git, a shared web directory or a cloud-synced folder. The application creates the profile directory with owner-only permissions and writes the file atomically with mode `0600` on POSIX.

The initial cosine threshold `0.363` is an OpenCV reference baseline, not a C.U.T.Y.-calibrated threshold. Matching is blocked by default; only set `CUTY_FACE_MATCH_CALIBRATED=1` after tuning threshold and margin with separate, consented enrollment and non-match sessions in the robot's real lighting and camera position. Do not lower the threshold merely to force a match. The face detector and SFace both need to be available; Haar fallback does not provide the five YuNet landmarks required for SFace alignment, so recognition fails closed in that case.

`CUTY_GEMINI_VISION_MODEL` selects the image understanding model and defaults to `gemini-3.8-flash`; it uses the existing Gemini API key and is only called for an explicit visual question. For OpenAI Realtime sessions, image description is not wired to Gemini automatically: configure the existing provider as Gemini to use this feature. The Gemini Live API accepts image frames as JPEG/PNG, but this implementation sends a single still image only when the user asks; it does not stream video.

## Consent and privacy

Enrollment prompt: “Puedo guardar varias plantillas faciales solo en este Raspberry Pi; no guardaré fotos.” The user must then say a phrase equivalent to “Confirmo guardar mi rostro y llámame [nombre]”. A cancellation or an invalid confirmation stores nothing. Forget requires a second phrase equivalent to “Confirmo, olvida mi rostro”. A low-confidence face is not deleted. `¿Quién soy?` never asks Gemini to identify a person.

The system masks rectangles returned by the current detector before a requested image is sent to Gemini. This prevents detected face regions from being sent, but a detector can miss a face; therefore the cloud request is **not a guarantee that all biometric pixels are removed**. If that residual risk is unacceptable, do not use cloud visual descriptions in a scene containing people. Embeddings and enrollment images are never sent to Gemini or the website.

The profile file contains sensitive biometric templates and a chosen display name. Local disk permissions protect against other unprivileged OS users, but root and processes running as the robot account can access it. Deleting a profile removes it from the local file; this is not a forensic secure erase of flash storage or backups.

## Resource and hardware validation

Snapshot conversion, JPEG encoding, Gemini requests, SFace enrollment and comparison are outside the display render loop. Recognition IPC and SFace work run off the voice asyncio loop. The existing camera detector loop continues as before; color conversion happens only when requested. No CPU, memory or latency figures are claimed because this implementation has not been measured on the Pi 5.

Tests use synthetic pixel arrays, fake detector observations, fake voice/provider objects and temporary profile files. No authorized human sample images were included in the repository, so biometric accuracy has not been tested. Before enabling enrollment on the robot, validate the SFace OpenCV build, YuNet frame alignment, camera/lighting quality, profile permissions, thresholds, voice confirmation, capture behavior while the animated face and audio are running, Pi resource use, and network-loss recovery. The physical camera/voice/display/audio combination was not exercised in this implementation session. Head-follow remains simulation only.

## References

- [Gemini Live API image/video input](https://ai.google.dev/gemini-api/docs/live-api/capabilities)
- [OpenCV Zoo SFace model and five-point alignment](https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface)
- [OpenCV face recognition threshold notes](https://github.com/opencv/opencv/blob/5.x/doc/tutorials/dnn/dnn_face/dnn_face.markdown)
