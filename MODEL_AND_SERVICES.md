# Model and services

## Optional language model

The optional provider is Groq's OpenAI-compatible chat completions API, called through the official `groq` Python client. The default model ID is `openai/gpt-oss-20b`, configurable with `GROQ_MODEL`; confirm the ID is currently available to your account in the [Groq model catalog](https://console.groq.com/docs/models). The model receives only the property name, location, price, property type, highlights, and call to action. It does not receive uploaded photographs. The prompt requests short JSON captions and explicitly forbids unsupported claims. The code validates shape and rejects new numeric claims; this reduces, but cannot eliminate, the chance of an unsupported non-numeric phrase. Review AI captions before publishing.

Groq's model list and [deprecation page](https://console.groq.com/docs/deprecations) change over time. API access, quotas, and cost depend on the user's current account and model; do not assume a particular free quota. No API key is needed for the baseline experience. A missing key, bad key, unavailable model, malformed response, timeout, provider error, or rate limit falls back to templates.

## Video pipeline

Pillow decodes and validates JPG/PNG/WEBP uploads, prepares each photo with overscan for smooth camera moves, and draws premium navy, champagne and teal cards. The cards appear during the exact sentence that names the fact. `edge-tts` uses Microsoft Edge's online text-to-speech service with a configurable male neural voice. Only the generated narration script is sent to the speech service; photos are not. The optional Pixabay track, “Easy Travel_medium 2” by Grand_Project, is lowered under speech and faded at the start and end. The [track page](https://pixabay.com/music/acoustic-group-easy-travel-medium-2-332847/) identifies it as registered with YouTube Content ID; consult the page and license details when publishing. Frames are streamed to FFmpeg through `imageio-ffmpeg`, which encodes H.264 and AAC audio in broadly compatible formats. The streaming approach keeps memory use predictable. The newest result is kept in `output/` for download.

## Data and privacy

Video rendering is local. When the optional Groq key is configured, only listing text is sent to the provider for caption generation; photos are never uploaded by this application. Keep `.env` private. Provider handling is governed by the provider's current terms and privacy policy.
