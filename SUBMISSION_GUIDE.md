# Safar submission guide

This guide maps the project to the candidate submission requirements and gives a short, repeatable demo. The runnable app and source code are in this folder; start with [README.md](README.md) for installation and setup. For a fuller technical description, see [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md).

## Submission checklist

- [x] **Working prototype:** `app.py` runs the Safar Streamlit application. `src/` contains validation, caption generation, and video rendering code.
- [x] **Source code and setup instructions:** Python source, pinned dependencies in `requirements.txt`, configuration template in `.env.example`, and install/configure/run instructions in [README.md](README.md).
- [x] **Sample input:** `src/sample_data/property.json` contains fictional listing information. For a live demo, use this data and four to eight photos you are authorized to use.
- [x] **Sample output:** `output/safar_sample.mp4` is a playable sample. It uses original illustrated scenes to show the motion and layout without presenting them as real property photos. Generate a new sample with `python scripts/create_sample_video.py`.
- [x] **Demo and explanation:** See the short walkthrough and explanation below.
- [x] **AI, libraries, and external services:** See [MODEL_AND_SERVICES.md](MODEL_AND_SERVICES.md). Groq is optional; the default caption path works offline. The soundtrack is from Pixabay and is documented there and in the README.
- [x] **Privacy:** The sample listing is fictional. Do not submit `.env`, API keys, customer information, or photos without permission. `.env` is excluded by `.gitignore`; `.env.example` contains placeholders only.

## Two-minute demo

1. Create and activate a virtual environment, install dependencies, and run `streamlit run app.py` as described in the README. Leave `GROQ_API_KEY` blank to demonstrate the offline path.
2. Enter the fictional sample listing: **The Fern House**, **Baner, Pune**, **Independent house**, **₹1.25 crore**, with highlights **Three bedrooms**, **Private garden**, **Recently renovated**, and **Covered parking**. Use the fictional call to action in `src/sample_data/property.json` or replace it with “Get in touch to learn more.”
3. Select four to eight permitted JPG, PNG, or WEBP photos, choose a video orientation, then create the film. For a quick no-upload preview, play `output/safar_sample.mp4`.
4. Point out the varied camera movement, scene dissolves, readable listing captions, fixed background music, preview, and MP4 download.

## Brief approach

Safar turns listing details and ordered photos into a short property video. Streamlit provides the form and preview; validation checks uploaded image contents and size; deterministic templates produce captions from the supplied facts. If a Groq key is configured, the optional language model can rephrase those facts. The renderer prepares each image with overscan, animates a pan or zoom, draws a high-contrast caption panel, blends scene changes, and streams frames to FFmpeg for MP4 encoding.

The local template route avoids an external API and does not upload photos. The optional Groq request contains listing text only. The sample video uses illustrated scenes so it can be shared without real listing imagery.

## Key decisions and limitations

- Listing facts come from the user; captions do not inspect photos. Confirm every claim and image order before publishing.
- Groq is optional and can be unavailable due to credentials, model access, connectivity, or rate limits; the app falls back to local templates.
- The app does not include narration, accounts, cloud storage, or post-generation scene reordering.
- The soundtrack is “Easy Travel_medium 2” by Grand_Project from Pixabay. Its page marks it as registered with YouTube Content ID; review the [track page](https://pixabay.com/music/acoustic-group-easy-travel-medium-2-332847/) and [license](https://pixabay.com/service/license-summary/) before public distribution.

## Before sharing the folder

Keep the source, `requirements.txt`, README, `.env.example`, `MODEL_AND_SERVICES.md`, this guide, sample JSON, required soundtrack asset, and sample MP4 together. Exclude `.env`, virtual environments such as `ronee/` or `.venv/`, caches, and any real customer media or secrets. Check the final archive contents before uploading.
