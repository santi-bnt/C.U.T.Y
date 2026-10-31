# C.U.T.Y LLM

`provider.py` defines the working provider boundary and normalized events. `openai_provider.py` preserves OpenAI Realtime; `gemini_provider.py` preserves the current Gemini Live default. `web_search.py` preserves the Gemini custom search tool path.

The architecture permits cloud providers and a future local provider. `local_provider.py` is only a TODO: no fallback selection, local model download, or inference engine has been added.

Providers exchange audio, transcription, and tool events with brain/audio. They do not control motors or render the face. Shared robot UART documents are not the AI tool event schema.
