# C.U.T.Y — Phase 1

C.U.T.Y is a small voice companion running on a Windows PC. Speak into the computer microphone and hear a streamed reply through the computer speakers. A live audio session keeps conversational context until you quit. No robot hardware is used. Gemini Live is the default provider because its selected native-audio model has a limited free API tier; OpenAI remains optional.

## Windows 11 setup

In PowerShell, from the repository root, first run `cd raspberry`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use `.\.venv\Scripts\python.exe` in place of `python` for the commands below.

Create a free-tier API key in [Google AI Studio](https://aistudio.google.com/app/apikey). Keep the project on the Free tier if you do not want billing. Enter the key for the current PowerShell session:

```powershell
$env:GEMINI_API_KEY = Read-Host "Enter your Gemini API key"
```

Or copy `.env.example` to `.env` and replace `your_key_here` with the real value. `.env` is ignored by Git. An existing `GEMINI_API_KEY` environment variable takes precedence over `.env`. The key is never logged. Do not share it or commit it. A previously set `OPENAI_API_KEY` does not affect the default Gemini provider.

List audio devices without an API key:

```powershell
python -m cuty --list-audio-devices
```

To check whether Windows is delivering your voice to C.U.T.Y, run this without an API key and speak normally for three seconds:

```powershell
python -m cuty --test-microphone
```

`Peak` and `RMS` should rise above zero while you speak. This test does not save or transmit the recording. If the level stays near zero, check Windows microphone privacy permissions, mute/input volume, and the chosen device.

Choose device indices from that list if the defaults do not work:

```powershell
$env:CUTY_AUDIO_INPUT_DEVICE = "1"
$env:CUTY_AUDIO_OUTPUT_DEVICE = "4"
```

At startup C.U.T.Y opens each selected device briefly to check that it works. If a Windows default uses a failing MME driver, it tries another interface for the same named device. Device indices can change when a headset or other audio device is connected.

Start C.U.T.Y:

```powershell
python -m cuty
```

Press ENTER to start recording, speak, and press ENTER again to stop. C.U.T.Y streams its spoken answer. Repeat for another turn; say your name, then ask it to recall your name. Type `q` and ENTER at the idle prompt to quit. The current mode waits for each answer before you can speak again.

C.U.T.Y is instructed to answer in the language of your latest spoken question automatically, switching between turns (English in, English out; Spanish in, Spanish out; likewise for other languages supported by the voice model). An explicit request for a particular response language takes priority. Mixed-language questions use their main language. This applies to AI replies; the fixed local thinking asides described below are still Spanish. Restart the app after changing the instructions in `src/cuty/brain/personality.py` so a new session receives them.

During waits longer than 1.8 seconds, C.U.T.Y can say a short creative Spanish aside, such as "Estoy conectando los puntitos" or "Estoy cocinando una idea". It stops the aside when the answer arrives, stays in `THINKING`, and says at most two phrases per turn, separated by five seconds. Fast replies have no filler. `src/cuty/audio/thinking.py` contains the editable phrase list. The phrases use a separate Mexican Spanish voice, not Gemini's voice, through [Edge TTS](https://github.com/rany2/edge-tts), which needs internet but no additional API key. Only the fixed phrases are sent to this service, never microphone recordings or conversation contents. They are prepared in the background and cached in memory for the session; if the service fails, normal conversation still works without asides.

In a successful turn, expect `[AI] Connected to Gemini Live` once, then `[CUTY] STATE -> LISTENING`, `THINKING`, `SPEAKING`, and `IDLE`. `[CUTY FACE]` lines show baseline expressions and any emotion chosen by the model.

The default model is `gemini-3.8-live`, Google's current stable Live model for low-latency voice agents. Its audio input and output are listed as free on the Gemini API Free tier, subject to quotas. Free-tier content may be used to improve Google products. Check Google's [models](https://ai.google.dev/gemini-api/docs/models) and [pricing](https://ai.google.dev/gemini-api/docs/pricing) pages for current availability and limits. Do not enable billing on the AI Studio project if you want a firm no-charge boundary.

Gemini can call `search_web` for current information through the public DDGS search library, without another API key or a Google Search API quota. Ask, for example, "Busca en internet cuál es la versión estable actual de Python y dime la fuente." C.U.T.Y replies by voice and logs actual queries and source links as `[WEB]`. Ordinary conversation does not need a search; a lookup may take longer. Searches return public page excerpts, not full browser sessions or actions on websites. The public search engines can rate-limit or become unavailable; C.U.T.Y reports an unsuccessful search instead of inventing a verified answer. This integration avoids the Gemini Live Google Search quota restriction observed on the configured free project. The optional OpenAI adapter does not enable this search tool.

## Tests

```powershell
python -m pytest -q
```

Tests use fakes and never call either AI API or require audio hardware. A real voice test requires a valid Gemini key, an accessible microphone and speaker, network access, and free-tier model access in your account. Override the Gemini model with `CUTY_GEMINI_MODEL` only if Google's availability changes.

The CLI logs connection and state changes, expression events, assistant transcripts, and Gemini's input transcription as `Escuché: ...`. If the local microphone test shows voice but no `Escuché` line appears during a turn, check that you spoke after the first ENTER and pressed ENTER again only after finishing. If microphone capture or speaker playback fails, check Windows microphone permission and try a different device index. If a connection fails temporarily, startup retries three times with short exponential delays. A disconnect during a turn ends the program so it does not silently lose session memory; start it again for a new session.

## Architecture

`src/cuty/brain/` owns conversation and states; `llm/` owns both cloud providers and web lookup; `audio/` owns microphone, speaker, and thinking asides. `src/cuty/main.py` is the entry point and `app.py` wires the CLI. `face/` contains working expression events and a console sink, not a screen renderer. Other robot modules are placeholders; see [architecture](../docs/architecture.md).

Baseline expressions follow `IDLE`, `LISTENING`, `THINKING`, and `SPEAKING` states. The model may call `set_expression` for a temporary emotion. Invalid tool arguments are rejected and returned to the model without emitting a robot event. No keyword-based emotion matching is used. There is no serial transport or defined UART protocol in this phase.

Gemini Live uses explicit activity boundaries: the first microphone chunk starts the user turn, and ENTER sends its end immediately. This avoids a separate server-side silence wait and prevents premature responses during a pause. Input is native 16 kHz PCM and output is 24 kHz PCM. Server events and speaker playback run independently, so expression tool results are submitted while audio plays. Expression calls explicitly use blocking mode so Gemini resumes speech after the result instead of silently completing an expression-only turn. The CLI logs `Primera voz en ... s` from the end of recording to the first playback chunk and reports an error if no voice arrives in 15 seconds or the server finishes without audio. The session keeps context in memory on the live connection. There is no long-term memory, wake word, hands-free turn control, or barge-in in Phase 1.

Implementation references: [Gemini Live capabilities](https://ai.google.dev/gemini-api/docs/live-api/capabilities) and [Gemini Live tools](https://ai.google.dev/gemini-api/docs/live-api/tools).

To use the optional OpenAI provider instead, set `CUTY_AI_PROVIDER=openai` and `OPENAI_API_KEY` in the environment; its default model is `gpt-realtime-2.1`. OpenAI API usage is billed separately. The earlier OpenAI integration and tests remain available.

## Later Raspberry Pi OS deployment

The same Python package is intended to install on 64-bit Raspberry Pi OS:

```bash
git clone <repository-url>
cd <repository-directory>/raspberry
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export GEMINI_API_KEY='your-real-key'
python -m cuty
```

The sample `systemd/cuty.service` is a placeholder for a later phase. This Phase 1 CLI needs keyboard input, so the unit should not be activated until a noninteractive interaction mode is added and tested on the Pi.

## Raspberry touchscreen

The existing [touch menu, demo face and Wi-Fi panel](touchscreen/README.md) are preserved separately in `touchscreen/`. This voice application is not yet connected to that demo. Screen dependencies are in `touchscreen/requirements.txt` and are not required for Windows voice development. Setup helpers now live in `scripts/` within this Raspberry directory.
