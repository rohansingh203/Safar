"""Streamlit interface for Safar property films."""

import json
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.script_generator import generate_captions
from src.validation import validate_image, validate_property
from src.video_generator import build_voice_segments, generate_video

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
load_dotenv(BASE_DIR / ".env")

st.set_page_config(page_title="Safar · Property Film Studio", page_icon="◧", layout="wide")
st.markdown("""<style>
.stApp {background:#f2f0e9;color:#172621;font-family:'Segoe UI',Arial,sans-serif}
header[data-testid="stHeader"] {background:transparent}
section.main > div {max-width:1440px;padding-top:1.4rem;padding-bottom:3rem}
h1,h2,h3 {font-family:'Segoe UI',Arial,sans-serif;letter-spacing:-.045em;color:#172621}
.hero {position:relative;overflow:hidden;background:#142a27;padding:2.1rem 2.5rem;border-radius:28px;color:#fff;margin-bottom:1.15rem;min-height:235px;box-shadow:0 18px 44px #19352b20}
.hero:after {content:'';position:absolute;width:320px;height:320px;border:1px solid #d4f07b55;border-radius:50%;right:8%;top:-165px;box-shadow:0 0 0 34px #d4f07b12,0 0 0 72px #d4f07b0a}
.brand {display:flex;align-items:center;gap:.65rem;font-weight:800;letter-spacing:.12em;font-size:.82rem;color:#f5f4ed}
.brand-mark {display:inline-grid;place-items:center;background:#d6f17c;color:#182722;border-radius:9px;width:28px;height:28px;font-size:1rem;letter-spacing:0}
.brand-tag {font-size:.62rem;color:#adc2b8;border:1px solid #6a8175;border-radius:99px;padding:.28rem .55rem;letter-spacing:.11em}
.hero-kicker {margin-top:1.5rem;text-transform:uppercase;letter-spacing:.18em;font-size:.65rem;color:#d6f17c;font-weight:700}
.hero h1 {color:#fff;font-size:clamp(2.1rem,4.4vw,3.7rem);line-height:1.02;margin:.45rem 0 .55rem}
.hero h1 em {font-family:Georgia,serif;font-weight:400;color:#d6f17c;letter-spacing:-.055em}
.hero p {color:#c5d2cb;font-size:.96rem;margin:0;max-width:560px}
.hero-stamp {position:absolute;z-index:1;right:9%;bottom:2rem;color:#e8eee8;text-align:center;transform:rotate(-8deg);border:1px solid #b7c9bd77;padding:.8rem 1rem;border-radius:50%;font-size:.62rem;letter-spacing:.15em;line-height:1.6}
.quote-card {display:flex;align-items:center;gap:1rem;background:#e4e7d8;border:1px solid #d7dbc8;border-left:4px solid #9aaa4d;border-radius:16px;padding:.8rem 1.1rem;margin:.25rem 0 1.3rem}
.quote-mark {font-family:Georgia,serif;font-size:2.7rem;line-height:.8;color:#82933d}
.quote-text {font-family:Georgia,serif;font-style:italic;font-size:1.02rem;color:#303c32}
.quote-credit {margin-left:auto;white-space:nowrap;font-size:.62rem;font-weight:800;letter-spacing:.13em;color:#5d6940}
.step-head {display:flex;align-items:center;gap:.7rem;font-weight:750;font-size:1.04rem;letter-spacing:-.02em;margin:.2rem 0 .6rem}
.step-num {display:inline-grid;place-items:center;background:#d6f17c;color:#192a24;border-radius:50%;width:27px;height:27px;font-size:.75rem}
.step-head {color:#263b31}
.stFileUploader small {color:#667063}
div[data-testid="stHorizontalBlock"] {align-items:flex-start}
div[data-testid="stVideo"] {border-radius:18px;overflow:hidden;box-shadow:0 12px 32px #19352b20}
div[data-testid="stForm"] {background:#fffefa;padding:1.3rem 1.45rem 1.15rem;border:1px solid #e3e0d5;border-radius:22px;box-shadow:0 9px 24px #29392d0a}
div[data-testid="stFileUploader"] {background:#fffefa;border:1px dashed #a7ad9c;border-radius:18px;padding:.7rem}
div[data-testid="stFileUploader"] section {border:0}
div[data-testid="stTextInput"] input,div[data-testid="stTextArea"] textarea,div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {border-radius:11px;background:#fbfaf6}
div.stButton>button,div.stFormSubmitButton>button {border-radius:12px;font-weight:750;min-height:2.85rem;transition:transform .18s,box-shadow .18s}
div.stFormSubmitButton>button {background:#d6f17c;color:#172621;border:0}
div.stFormSubmitButton>button:hover {background:#c4e75f;color:#172621;transform:translateY(-1px);box-shadow:0 8px 20px #8da83f33}
div[data-testid="stAlert"] {border-radius:14px}
div[data-testid="stProgress"] > div > div {background:#91a441}
.stCaption {color:#626c62}
@media(max-width:800px){.hero {padding:1.5rem;min-height:215px}.hero-stamp {right:4%;bottom:1rem;transform:scale(.8) rotate(-8deg)}.quote-card {flex-wrap:wrap;gap:.45rem}.quote-credit {margin-left:0}section.main > div {padding-left:1rem;padding-right:1rem}}
</style>""", unsafe_allow_html=True)

st.markdown('<div class="hero"><div class="brand"><span class="brand-mark">S</span> SAFAR <span class="brand-tag">PROPERTY FILM STUDIO</span></div><div class="hero-kicker">A new way to show people home</div><h1>Every home<br><em>has a journey.</em></h1><p>Turn your listing photos into a moving property film, ready to share wherever buyers are looking.</p><div class="hero-stamp">SCROLL<br>INTO<br>HOME</div></div>', unsafe_allow_html=True)
st.markdown('<div class="quote-card"><span class="quote-mark">“</span><span class="quote-text">Some places stay with you. Make your listing one of them.</span><span class="quote-credit">— SAFAR STUDIO</span></div>', unsafe_allow_html=True)

left, right = st.columns([1.05, .95], gap="large")
with left:
    st.markdown('<div class="step-head"><span class="step-num">01</span> The listing</div>', unsafe_allow_html=True)
    with st.form("listing"):
        property_name = st.text_input("Property name", placeholder="e.g. The Fern House")
        location = st.text_input("Location", placeholder="e.g. Baner, Pune")
        a, b = st.columns(2)
        with a:
            property_type = st.selectbox("Property type", ["Apartment", "Villa", "Independent house", "Plot", "Commercial property"])
            price = st.text_input("Price (optional)", placeholder="₹1.25 crore")
        with b:
            contact = st.text_input("Contact or call to action", placeholder="Call Maya at 90000 12345")
            format_name = st.selectbox("Video format", ["Landscape · 16:9", "Vertical · 9:16"])
        features_text = st.text_area("Highlights · one per line", placeholder="Three bedrooms\nPrivate garden\nRecently renovated", height=105)
        voiceover_enabled = st.checkbox("Add a natural male voice cover", value=True, help="A neural English narrator reads a short, fact-based property script.")
        voice_options = {
            "Guy · warm American": "en-US-GuyNeural",
            "Christopher · confident American": "en-US-ChristopherNeural",
            "Davis · conversational American": "en-US-DavisNeural",
        }
        voice_label = st.selectbox("Narrator voice", list(voice_options), disabled=not voiceover_enabled)
        st.caption("Online speech synthesis sends only the generated script text to Microsoft’s speech service. Your photos stay on this computer.")
        background_music = st.checkbox("Include soft background music", value=True)
        quality = st.selectbox("Export quality", ["1080p · Premium", "720p · Faster"])
        submitted = st.form_submit_button("Create my property video  →", type="primary", use_container_width=True)

with right:
    st.markdown('<div class="step-head"><span class="step-num">02</span> The frames</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Choose 4–8 photos · JPG, PNG or WEBP · up to 15 MB each", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key="property_photos")
    st.caption("Your photos stay on this computer. Upload order becomes the story order.")
    st.markdown('<div style="display:inline-flex;gap:.5rem;align-items:center;background:#e7e9db;color:#48513e;padding:.4rem .7rem;border-radius:999px;font-size:.72rem;font-weight:700;letter-spacing:.06em;margin:.2rem 0 .6rem">◉ &nbsp;30 FPS &nbsp;·&nbsp; 1080P &nbsp;·&nbsp; CINEMATIC MOVES &nbsp;·&nbsp; SYNCED VOICE</div>', unsafe_allow_html=True)
    st.caption("Every export opens with the six-second SAFAR brand intro before the listing scenes.")
    if uploaded:
        st.write(f"**{len(uploaded)} photo{'s' if len(uploaded) != 1 else ''} selected** · shown in scene order")
        cols = st.columns(4)
        for i, photo in enumerate(uploaded):
            with cols[i % 4]:
                st.image(photo, caption=f"{i + 1:02d} · {photo.name}", use_container_width=True)

if submitted:
    raw_images = [photo.getvalue() for photo in (uploaded or [])]
    errors = validate_property(property_name, location, len(raw_images))
    for photo, raw in zip(uploaded or [], raw_images):
        valid, message = validate_image(raw, photo.name)
        if not valid:
            errors.append(message)
    if errors:
        for error in errors:
            st.error(error)
        if not voiceover_enabled and not background_music:
            st.error("Choose a voice cover or background music so the video has an audio track.")
    else:
        features = [line.strip() for line in features_text.splitlines() if line.strip()]
        progress = st.progress(0, text="Preparing your listing…")
        captions, _caption_source = generate_captions(property_name.strip(), location.strip(), price.strip(), property_type, features, contact.strip(), len(raw_images))
        voice_segments = build_voice_segments(property_name.strip(), location.strip(), property_type, price.strip(), features, contact.strip()) if voiceover_enabled else None
        voice_text = " ".join(segment["text"] for segment in voice_segments) if voice_segments else None
        progress.progress(12, text="Preparing the male narrator and cinematic scenes…" if voice_text else "Captions ready · arranging your scenes…")
        output_path = OUTPUT_DIR / "safar_property.mp4"
        try:
            def update_render_progress(current, total):
                progress.progress(15 + int(80 * current / total), text=f"Rendering cinematic frame {current} of {total}…")

            video_bytes = generate_video(raw_images, captions, property_name.strip(), location.strip(), price.strip(), contact.strip(), output_path=output_path, vertical=format_name.startswith("Vertical"), progress_callback=update_render_progress, voiceover_segments=voice_segments, voice=voice_options[voice_label], include_music=background_music, resolution="1080p" if quality.startswith("1080p") else "720p")
            progress.progress(100, text="Your video is ready.")
            st.success("Your Safar film is ready.")
            st.video(video_bytes)
            st.download_button("Download Safar film", video_bytes, file_name="safar_property.mp4", mime="video/mp4", type="primary")
            with st.expander("Review scene captions"):
                for number, caption in enumerate(captions, 1):
                    st.write(f"**Scene {number}**  {caption}")
            if voice_text:
                with st.expander("Review voice cover"):
                    st.write(voice_text)
            st.caption(f"Saved locally to {output_path.relative_to(BASE_DIR)} · {len(video_bytes) / 1024 / 1024:.1f} MB")
        except Exception as error:
            progress.empty()
            st.error("Rendering did not finish. Check that the photos are valid and that FFmpeg is available, then try again.")
            st.exception(error)

with st.expander("Preview the Safar sample film"):
    sample = json.loads((BASE_DIR / "src" / "sample_data" / "property.json").read_text(encoding="utf-8"))
    st.write(f"**{sample['property_name']}** · {sample['location']} · {sample['price']}")
    st.write("Highlights: " + " · ".join(sample["features"]))
    sample_video = OUTPUT_DIR / "safar_sample.mp4"
    if sample_video.exists() and sample_video.stat().st_size:
        st.video(sample_video.read_bytes())
        st.download_button("Download illustrated sample", sample_video.read_bytes(), file_name="safar_sample.mp4", mime="video/mp4")
    st.caption("Use this preview to see Safar's motion and soundtrack. It uses fictional details and original illustrations; upload your own 4–8 listing photos for a real property film.")

st.divider()
st.caption("SAFAR · PROPERTY FILM STUDIO · Made to move")
