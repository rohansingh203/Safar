# Safar project overview

## What Safar does

Safar is a local-first property video maker. A user enters listing details, adds four to eight property photos, chooses landscape or vertical video, and generates a 20–40 second MP4. The six-second animated SAFAR brand intro leads into fact-based cards synchronized to a male neural voiceover, animated photo framing, transitions, and optional background music.

## How a video is made

1. **Collect listing details:** The Streamlit page gathers the property name, location, type, optional price, highlights, contact line, orientation, and photos.
2. **Validate inputs:** `src/validation.py` checks that required text is present, the photo count is four to eight, and each upload is a valid JPG, PNG, or WEBP image no larger than 15 MB.
3. **Write captions:** `src/script_generator.py` uses built-in templates by default. If the user configures a Groq API key, it can ask the selected language model to phrase captions using only the submitted listing facts. Invalid responses, unsupported new numbers, or provider errors fall back to the templates.
4. **Animate scenes:** `src/video_generator.py` uses Pillow to resize and draw each photo and its caption panel. It creates a smooth push or pan by cropping successive frames from an overscanned image, then blends scenes with short dissolves.
5. **Add a voice cover:** Edge TTS synthesizes each sentence using a configurable English male neural voice. Sentence audio durations provide timing for matching on-screen property cards. The generated script text is sent to the online speech service; uploaded photos stay local.
6. **Lead with SAFAR:** The reusable 180-frame animation introduces the brand for exactly six seconds. A generated instrumental whoosh plays first; the property music and narration start afterward.
7. **Encode and deliver:** `imageio-ffmpeg` streams 30 FPS 1080p (or optional 720p) frames to FFmpeg, which encodes H.264 video and AAC audio into an MP4. Background music is optional and mixed beneath speech. The finished video is previewed in the app, offered for download, and saved under `output/`.

## Models and external services

| Component | Use in Safar | Required? |
|---|---|---|
| Groq API with configurable model ID (default in code: `openai/gpt-oss-20b`) | Optional rewriting of listing captions from text facts | No; local caption templates work offline |
| Pixabay track “Easy Travel_medium 2” by Grand_Project | Optional music track; stored at `assets/safar_travel.mp3`, lowered beneath voice | No |
| FFmpeg through `imageio-ffmpeg` | Encodes video and audio into MP4 | Yes |
| Edge TTS | Optional configurable English male neural voiceover | No, but internet access is required when narration is enabled |

Safar does **not** use an image-generation model, image-understanding model, or AI video-generation model. The photo movement and scene transitions are created with ordinary image-processing code. The sample film uses original vector illustrations rather than AI-generated property photos.

The optional Groq call sends the property name, location, price, type, features, and contact line. Uploaded photos are not sent to Groq by this application. Model IDs, provider access, and provider terms can change; check [MODEL_AND_SERVICES.md](MODEL_AND_SERVICES.md) and the linked provider documentation before presenting a live AI request. The selected Pixabay track is marked as registered with YouTube Content ID; review its [track page](https://pixabay.com/music/acoustic-group-easy-travel-medium-2-332847/) and the [Pixabay license](https://pixabay.com/service/license-summary/) before distribution.

## Libraries and project files

- **Streamlit** — web interface, upload form, progress, preview, and download.
- **Pillow** — image validation, resizing, cropping, and caption graphics.
- **NumPy** — frame conversion for the video encoder.
- **imageio-ffmpeg** — FFmpeg executable and frame streaming.
- **Groq Python client** — optional API access for caption wording.
- **edge-tts** — online neural voiceover with selectable male English voices.
- **python-dotenv** — reads local configuration from `.env`.

Main files:

- `app.py` — interface and end-to-end workflow.
- `src/validation.py` — listing and image checks.
- `src/script_generator.py` — offline captions and optional Groq captions.
- `src/video_generator.py` — photo animation, overlays, soundtrack, transitions, and encoding.
- `src/sample_data/property.json` — fictional sample listing.
- `output/safar_sample.mp4` — illustrated sample output.
- `requirements.txt` — pinned Python package versions.
- `README.md` — installation, configuration, and run instructions.

## Limitations

- Captions are based on typed details; Safar does not verify property facts or understand what appears in photos. Review all text and visuals before publishing.
- Groq is optional and may be unavailable; the template path does not require network access.
- Photos stay on the local machine in the app's current flow. If Groq is configured, listing text is sent to Groq for caption generation.
- Online narration depends on service availability and internet access. The app has no user accounts, cloud storage, or post-generation scene reordering.
- Video rendering uses local CPU resources; render time depends on photo size and computer performance.
