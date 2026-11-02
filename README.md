# 🎬 SAFAR — Property Film Studio

**Turn property photos into cinematic real estate videos with AI-powered captions and narration.**

SAFAR is a local-first property video generation application that transforms property listing details and 4–8 photos into a professional, shareable MP4 property film.

It automates camera movements, scene transitions, animated information cards, captions, voice narration, and background music to help real estate agents create engaging property advertisements.

---

## ✨ Key Features

- **Photo-to-Video Conversion:** Convert 4–8 property photos into a cinematic video.
- **Dynamic Camera Movements:** Different zoom and pan effects for individual scenes.
- **Smooth Transitions:** Professional dissolves between property scenes.
- **AI-Powered Captions:** Optional Groq integration for generating property captions.
- **Offline Caption Generation:** Built-in templates work without an API key.
- **AI Voice Narration:** Generate property narration using Edge TTS.
- **Animated Information Cards:** Display location, price, property highlights, and enquiry details.
- **Background Music:** Cinematic background soundtrack with audio fading.
- **Multiple Video Formats:** Export in landscape (16:9) or vertical (9:16).
- **HD Video Export:** Choose between 720p and 1080p.
- **MP4 Download:** Preview and download the generated property film.
- **Local-First Processing:** Property photos are processed locally on your computer.

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | User interface |
| Pillow (PIL) | Image processing and animated text cards |
| Groq API | Optional AI caption generation |
| Edge TTS | Voice narration |
| FFmpeg | Video encoding and audio processing |
| imageio-ffmpeg | FFmpeg integration |
| NumPy | Frame and image processing |

---

## ⚙️ How It Works

1. Enter property information such as name, location, price, and highlights.
2. Upload 4–8 property photographs.
3. Select the video orientation and resolution.
4. SAFAR generates captions using local templates or optionally Groq.
5. The narration service generates voice audio from the property script.
6. The video renderer applies camera movements, animated cards, and transitions.
7. FFmpeg combines video, narration, and background music.
8. Preview and download the final MP4 video.

---

## 🏗️ Project Architecture

```text
SAFAR/
│
├── app.py
│
├── src/
│   ├── validation.py
│   ├── script_generator.py
│   └── video_generator.py
│
├── assets/
│   └── safar_travel.mp3
│
├── scripts/
│   ├── create_sample_video.py
│   └── create_soundtrack.py
│
├── tests/
│
├── output/
│
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── SUBMISSION_GUIDE.md
├── PROJECT_OVERVIEW.md
└── MODEL_AND_SERVICES.md
```

### Main Components

- `app.py` — Streamlit application and user interface.
- `validation.py` — Validates uploaded images and listing details.
- `script_generator.py` — Generates property captions using local templates or Groq.
- `video_generator.py` — Creates animated scenes, narration, transitions, and the final video.
- `assets/` — Stores background music and other project assets.
- `tests/` — Contains automated project tests.
- `output/` — Stores generated MP4 videos.

---

## 🚀 Installation and Setup

### Requirements

- Python 3.12
- Windows 10/11
- Internet connection for optional AI captions and voice narration.

### Step 1: Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd SAFAR
```

### Step 2: Create a Virtual Environment

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```powershell
Copy-Item .env.example .env
```

Add your Groq API key to `.env` if you want AI-generated captions.

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=your_available_model_id
```

**Note:** Groq integration is optional. SAFAR works with built-in caption templates when no API key is configured.

Never upload your `.env` file or expose API keys publicly.

### Step 5: Run the Application

```powershell
streamlit run app.py
```

Open the local URL displayed in your terminal, normally:

`http://localhost:8501`

---

## 🎥 Sample Output

SAFAR generates an MP4 property advertisement featuring:

- Animated SAFAR introduction.
- Cinematic property photo sequences.
- Individual camera movements.
- Smooth scene transitions.
- Property information cards.
- Voice narration with synchronized captions.
- Background music.
- Final enquiry and contact panel.

A sample technical video is available at:

`output/safar_sample.mp4`

The sample uses original vector illustrations to demonstrate video rendering and is not actual property photography.

---

## 🧪 Testing

Run the automated test suite:

```powershell
python -m unittest discover -s tests -v
```

Tests cover:

- Required listing fields.
- Image count validation.
- Unsupported and malformed images.
- Offline caption generation.
- AI generation success and failure.
- Camera movement and frame generation.
- MP4 decoding in landscape and portrait formats.

Live third-party service availability is not guaranteed by these tests.

---

## 🔐 Privacy and Data Handling

SAFAR follows a local-first processing approach.

- Property photos are processed locally.
- Groq receives listing text only when optional AI captions are enabled.
- The online TTS service receives narration script text.
- Photos are not uploaded to Groq or the TTS provider.
- No cloud storage or user account is required.
- Users can generate captions offline without an API key.

Avoid including sensitive customer information in third-party AI requests.

---

## ⚠️ Limitations

- Supports 4–8 images per video.
- Scene order follows the uploaded photo order.
- SAFAR does not currently inspect photographs using computer vision.
- Property facts and highlights must be supplied by the user.
- Voice narration requires an internet connection.
- Video rendering uses local CPU resources.
- Groq model access and rate limits depend on provider availability.
- The application does not currently provide cloud storage or user authentication.

---

## 🔮 Future Improvements

- Drag-and-drop scene reordering.
- AI-based property image analysis.
- Automatic property type detection.
- Multiple narration voices and languages.
- Custom branding, logos, and templates.
- More cinematic transition styles.
- Cloud-based video rendering.
- Saved projects and video history.
- Integration with real estate listing platforms.

---

## 🎯 Project Objective

The objective of SAFAR is to simplify real estate video marketing by converting ordinary property photographs and listing information into engaging cinematic advertisements through automation.

Instead of manually editing every property video, users can generate a complete promotional film through a simple interface.

---

## 👨‍💻 Developer

**Rohan Singh**

AI & Data Science Student

Developed as an AI-powered multimedia automation project.

---

## 📄 Additional Documentation

- `SUBMISSION_GUIDE.md` — Candidate deliverables, demonstration script, approach, and limitations.
- `PROJECT_OVERVIEW.md` — Architecture and technical explanation.
- `MODEL_AND_SERVICES.md` — AI models, libraries, and external services.

## 📜 Music Attribution

Background music: **Easy Travel_medium 2 — Grand_Project**

Source: [Pixabay Music](https://pixabay.com/music/acoustic-group-easy-travel-medium-2-332847/)

Used under the [Pixabay Content License](https://pixabay.com/service/license-summary/). The track is registered with YouTube Content ID.

---

**Built with Python, AI, and creativity.**

*SAFAR — Every property has a story. Give it a film.*
