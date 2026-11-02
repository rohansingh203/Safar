# Safar — Property Film Studio

Safar turns a property listing and 4–8 photos into a shareable MP4 property film. Each photo gets a different camera move, and scenes blend together. It is a local-first Streamlit app: photos are rendered on your computer; an optional Groq request sends listing text only to create captions. Without a key, the built-in caption templates work offline.

For the candidate deliverable checklist, short demo script, approach, and limitations, see [SUBMISSION_GUIDE.md](SUBMISSION_GUIDE.md). For a fuller explanation of the architecture and technologies, see [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md). For the AI, libraries, and external music service details, see [MODEL_AND_SERVICES.md](MODEL_AND_SERVICES.md).

## Run on Windows

Python 3.12 is the tested version. From PowerShell in this folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```

Open the local address shown by Streamlit (normally `http://localhost:8501`). To stop the server, press Ctrl+C in that PowerShell window. Leave `GROQ_API_KEY` blank for offline use. To enable Groq captions, add a key to `.env`; do not share or commit that file. `GROQ_MODEL` selects a model ID available to your account. If credentials, the selected model, connectivity, or rate limits cause an error, the app quietly uses the local templates.

## Make a video

1. Enter a fictional or real listing name and location. Add the price, contact call to action, and verified highlights if available.
2. Select 4–8 JPG, PNG, or WEBP photos (up to 15 MB each). The preview order is the video scene order.
3. Choose landscape (16:9) or vertical (9:16), then create the video.
4. Preview it in the page and download the MP4. The latest render is also saved to `output/safar_property.mp4`.

Every export opens with a six-second animated SAFAR identity sequence and original cinematic whoosh, then transitions to the first property photo. Narration and its synchronized information card begin after the intro. The renderer creates location, price, scene cards and a closing enquiry panel over smooth camera moves and dissolves. Each spoken sentence has a matching on-screen card timed to that sentence. By default, a configurable male neural voice creates a 14–34 second property segment from the details and up to five highlights. The online TTS service receives only the script text; photos remain local. Turn off the voice cover to export music only. Background music can also be disabled. Choose 1080p or a faster 720p export. The soundtrack is **“Easy Travel_medium 2” by Grand_Project**, from `assets/safar_travel.mp3`; its music level is lowered beneath narration and it fades at the beginning and end. The track is provided by [Pixabay](https://pixabay.com/music/acoustic-group-easy-travel-medium-2-332847/) under the [Pixabay Content License](https://pixabay.com/service/license-summary/); its page marks it as registered with YouTube Content ID. FFmpeg encodes H.264 video with broadly compatible `yuv420p` and AAC audio. Frames are streamed to FFmpeg to keep memory use predictable. Avoid putting sensitive customer information into a third-party AI prompt; captions can be generated locally with the key left blank.

## Sample listing

`src/sample_data/property.json` contains fictional details for **The Fern House** in Baner, Pune. `output/safar_sample.mp4` is a real, playable technical sample made from original vector illustrations, not property photography. It demonstrates motion, transitions, layout, and encoding; use real listing photos for a real advertisement. Recreate it with `python scripts/create_sample_video.py`.

## Tests

Run the project checks with:

```powershell
python -m unittest discover -s tests -v
```

Tests cover required fields, 4/6/8 image counts, malformed and unsupported images, offline captions, AI success and failure paths, changing camera frames, and MP4 decoding in both orientations. They do not exercise a live Groq account or guarantee the external provider is available.

## How it works

- `app.py` provides the listing form, photo previews, status, video preview, and download.
- `src/validation.py` checks required fields and verifies image contents, format, and size.
- `src/script_generator.py` creates fact-grounded local captions and can optionally ask Groq for alternate phrasing. Failed requests use the same deterministic templates.
- `src/video_generator.py` uses Pillow for animated text cards, Edge TTS for configurable male neural narration, and streams frames plus a balanced soundtrack mix through `imageio-ffmpeg` to the bundled FFmpeg encoder. It avoids loading a full video into memory.
- `scripts/create_soundtrack.py` is an unused earlier experiment that recreates the original plucked-string draft; Safar now uses the Pixabay track listed above.

The optional provider/model and current model catalog are documented by [Groq's model list](https://console.groq.com/docs/models) and [deprecation notes](https://console.groq.com/docs/deprecations). Model IDs, account access, rate limits, and pricing can change; configure a model available to your account. The baseline workflow has no API dependency or paid subscription requirement.

## Interview walkthrough

**Problem:** Agents often spend time turning listing facts and photos into short social video ads. Safar packages that repetitive production workflow into a small local tool.

**Demo:** Use the fictional Fern House details, choose four property photos, select vertical format, generate, play the result, then download it. Point out that the displayed photo order becomes the scene order. Keep `.env` without a key to demonstrate the reliable no-service path.

**Technical explanation:** Streamlit handles the browser interface. Pillow validates and prepares photos and draws legible text panels. Optional Groq text generation rewrites only facts supplied in the form; the local template path is deterministic and needs no network. The renderer streams frames to FFmpeg, which writes an H.264 MP4. Errors are caught at the UI boundary and unsupported uploads are rejected before rendering.

**Known limits:** Captions and narration use typed details; Safar does not inspect images or verify property facts. Scene order follows upload order and cannot currently be rearranged after upload. Narration requires internet access to the online speech service. The app has no cloud storage or accounts. Groq free access and model availability are subject to provider terms and may change. The local renderer uses CPU and render time depends on image size and hardware.

## Evaluation checklist

- **Problem and business relevance (20%)** — Listing fields and supplied photos produce a focused property advertisement.
- **Working implementation (30%)** — Validated uploads, real landscape/vertical MP4 rendering, in-page playback, and download are provided; run the documented tests locally.
- **AI/ML (20%)** — Optional configurable Groq caption rewriting is grounded in listing facts; offline templates keep the workflow usable without AI.
- **Code quality (15%)** — UI, validation, caption generation, and rendering are separated; dependencies are pinned; secrets and generated videos are ignored.
- **Usability and explanation (15%)** — Photo previews, clear errors, progress, fictional sample details, setup steps, and an interview demo script are included.
