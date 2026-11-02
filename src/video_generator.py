"""Premium property-film rendering with sentence-timed speech and information cards."""

import asyncio
import io
import math
import re
import subprocess
import tempfile
import wave
from pathlib import Path

import edge_tts
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

FPS = 30
BRAND_INTRO_SECONDS = 6
BRAND_INTRO_FRAMES = FPS * BRAND_INTRO_SECONDS
NAVY = (16, 28, 44)
CHARCOAL = (24, 37, 54)
GOLD = (214, 180, 119)
WHITE = (247, 247, 245)
TEAL = (105, 213, 206)
_BRAND_BASES = {}


def _sentence(text, title, detail=None, kind="detail"):
    return {"text": text, "title": title, "detail": detail or "", "kind": kind}


def build_voice_segments(property_name, location, property_type, price, features, contact):
    """Build spoken facts and their matching on-screen cards as one timed sequence."""
    article = "an" if property_type[:1].lower() in "aeiou" else "a"
    spoken_type = property_type[:1].lower() + property_type[1:] if property_type[:1].isalpha() else property_type
    segments = [
        _sentence(f"Welcome to {property_name}.", "PROPERTY FILM", property_name, "opening"),
        _sentence(f"This is {article} {spoken_type}.", "PROPERTY TYPE", property_type, "type"),
        _sentence(f"Located in {location}.", "LOCATION", location, "location"),
    ]
    for feature in [str(item).strip().rstrip(".?!") for item in features if str(item).strip()][:5]:
        spoken_feature = feature[:1].lower() + feature[1:] if feature[:1].isalpha() else feature
        segments.append(_sentence(f"A key feature is {spoken_feature}.", _feature_label(feature), feature, "feature"))
    if price:
        segments.append(_sentence(f"The listed price is {price}.", "ASKING PRICE", price, "price"))
    if contact:
        spoken_contact = contact.rstrip(".!?")
        if spoken_contact[:1].isalpha():
            spoken_contact = spoken_contact[:1].lower() + spoken_contact[1:]
        segments.append(_sentence(f"For more information, {spoken_contact}.", "ENQUIRE TODAY", contact, "closing"))
    else:
        segments.append(_sentence("Contact us today to learn more.", "ENQUIRE TODAY", "Contact us today", "closing"))
    return segments


def _feature_label(feature):
    normalized = feature.lower()
    if re.search(r"\b(bhk|bed(room)?s?)\b", normalized):
        return "BEDROOMS"
    if re.search(r"\b(bath(room)?s?|washroom)s?\b", normalized):
        return "BATHROOMS"
    if "kitchen" in normalized:
        return "KITCHEN"
    if any(word in normalized for word in ("sq ft", "sq. ft", "square feet", "area")):
        return "AREA"
    if any(word in normalized for word in ("garden", "balcony", "terrace", "pool", "parking", "view")):
        return "FEATURE"
    return "HIGHLIGHT"


def build_voice_script(property_name, location, property_type, price, features, contact):
    return " ".join(segment["text"] for segment in build_voice_segments(property_name, location, property_type, price, features, contact))


def _font(size, *, bold=False, serif=False):
    candidates = []
    if serif:
        candidates.extend(("C:/Windows/Fonts/georgiab.ttf" if bold else "C:/Windows/Fonts/georgia.ttf",))
    candidates.extend((
        "C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ))
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass
    return ImageFont.load_default()


def _cover_crop(image, size):
    width, height = size
    source = Image.open(io.BytesIO(image)).convert("RGB")
    # Slight overscan preserves a clean crop throughout the Ken Burns move.
    return ImageOps.fit(source, (round(width * 1.16), round(height * 1.16)), method=Image.Resampling.LANCZOS)


def _camera_frame(canvas, size, index, camera_t):
    width, height = size
    overscan = canvas.size
    eased = camera_t * camera_t * (3 - 2 * camera_t)
    moves = ((1.01, 1.12), (1.10, 1.025), (1.025, 1.11), (1.08, 1.02))
    zoom_start, zoom_end = moves[index % len(moves)]
    zoom = zoom_start + (zoom_end - zoom_start) * eased
    crop_w, crop_h = round(overscan[0] / zoom), round(overscan[1] / zoom)
    travel_x, travel_y = overscan[0] - crop_w, overscan[1] - crop_h
    pan_x = eased if index % 2 == 0 else 1 - eased
    pan_y = 0.3 + eased * 0.4 if index % 3 == 0 else 0.7 - eased * 0.4
    left, upper = round(travel_x * pan_x), round(travel_y * pan_y)
    return canvas.crop((left, upper, left + crop_w, upper + crop_h)).resize(size, Image.Resampling.LANCZOS)


def _brand_base(size):
    if size not in _BRAND_BASES:
        width, height = size
        image = Image.new("RGB", size)
        draw = ImageDraw.Draw(image)
        for y in range(height):
            p = y / max(1, height - 1)
            color = tuple(round(NAVY[channel] * (1 - p * 0.35) + CHARCOAL[channel] * p * 0.35) for channel in range(3))
            draw.line((0, y, width, y), fill=color)
        _BRAND_BASES[size] = image
    return _BRAND_BASES[size]


def _brand_intro_frame(size, frame_index):
    """Render one frame of the reusable six-second SAFAR identity opener."""
    width, height = size
    t = max(0.0, min(6.0, frame_index / FPS))
    frame = _brand_base(size).copy()
    draw = ImageDraw.Draw(frame, "RGBA")
    gold = (*GOLD, 150)
    # Restrained architectural elevations draw in from both edges during the opening beat.
    line_progress = min(1.0, t / 1.45)
    architectural_paths = [
        [(0.07, 0.76), (0.20, 0.52), (0.34, 0.76), (0.34, 0.91)],
        [(0.66, 0.90), (0.66, 0.57), (0.77, 0.57), (0.77, 0.90)],
        [(0.79, 0.90), (0.79, 0.44), (0.91, 0.44), (0.91, 0.90)],
        [(0.63, 0.57), (0.715, 0.45), (0.80, 0.57)],
    ]
    for path_index, points in enumerate(architectural_paths):
        reveal = max(0.0, min(1.0, line_progress * 1.35 - path_index * 0.08))
        for start, end in zip(points, points[1:]):
            x1, y1 = round(start[0] * width), round(start[1] * height)
            x2, y2 = round(end[0] * width), round(end[1] * height)
            draw.line((x1, y1, x1 + (x2 - x1) * reveal, y1 + (y2 - y1) * reveal), fill=gold, width=max(1, round(height * 0.0015)))
    # A few fine-lit windows add architectural depth without turning the mark into an icon.
    window_alpha = round(90 * line_progress)
    for column in range(3):
        for row in range(3):
            x = round(width * (0.805 + column * 0.035))
            y = round(height * (0.51 + row * 0.105))
            draw.line((x, y, x, y + round(height * 0.038)), fill=(*GOLD, window_alpha), width=max(1, round(height * 0.001)))
    # Subtle drifting dust catches the moving gold light.
    for particle in range(24):
        x = int((particle * 293 + t * (13 + particle % 11)) % width)
        y = int((particle * 137 + t * (4 + particle % 3)) % height)
        alpha = round(35 + 25 * (0.5 + 0.5 * math.sin(t * 1.2 + particle)))
        radius = max(1, round(height * 0.0011))
        draw.ellipse((x, y, x + radius * 2, y + radius * 2), fill=(*GOLD, alpha))
    frame = frame.convert("RGBA")
    # The wordmark scales in from a quiet, tracked typographic lockup.
    logo_t = max(0.0, min(1.0, (t - 1.45) / 1.25))
    if logo_t:
        eased = logo_t * logo_t * (3 - 2 * logo_t)
        font = _font(round(height * (0.082 + 0.009 * eased)), bold=True)
        logo_layer = Image.new("RGBA", size, (0, 0, 0, 0))
        logo_draw = ImageDraw.Draw(logo_layer)
        letters = "SAFAR"
        spacing = round(height * 0.014)
        char_widths = [logo_draw.textlength(char, font=font) for char in letters]
        total_width = sum(char_widths) + spacing * (len(letters) - 1)
        x = (width - total_width) / 2
        y = round(height * 0.34 + (1.0 - eased) * height * 0.018)
        alpha = round(255 * min(1.0, logo_t * 2.2))
        for char, char_width in zip(letters, char_widths):
            logo_draw.text((x, y), char, font=font, fill=(*WHITE, alpha))
            x += char_width + spacing
        # A fine gold rule and traveling highlight reveal the brand name.
        rule_y = round(height * 0.48)
        line_w = round(width * 0.27 * eased)
        x_left = round((width - line_w) / 2)
        logo_draw.line((x_left, rule_y, x_left + line_w, rule_y), fill=(*GOLD, round(alpha * 0.8)), width=max(1, round(height * 0.002)))
        sweep_t = max(0.0, min(1.0, (t - 2.0) / 1.25))
        sweep_x = round(width * (0.31 + 0.38 * sweep_t))
        logo_draw.line((sweep_x, y - round(height * 0.02), sweep_x + round(width * 0.018), rule_y + round(height * 0.012)),
                       fill=(255, 239, 202, round(180 * (1 - abs(sweep_t - 0.5) * 1.7))), width=max(2, round(height * 0.004)))
        frame = Image.alpha_composite(frame, logo_layer)
    # Two concise, sequential brand promises; no spoken line or voice is added to the intro.
    for phrase, start, end, y_ratio in (
        ("Every Property Has a Story.", 3.35, 4.02, 0.565),
        ("We Bring It to Life.", 4.05, 4.78, 0.625),
    ):
        reveal = max(0.0, min(1.0, (t - start) / 0.34))
        if reveal:
            alpha = round(255 * min(1.0, reveal * 1.7))
            font = _font(round(height * 0.035), serif=True)
            layer = Image.new("RGBA", size, (0, 0, 0, 0))
            layer_draw = ImageDraw.Draw(layer)
            bbox = layer_draw.textbbox((0, 0), phrase, font=font)
            x = (width - (bbox[2] - bbox[0])) // 2
            y = round(height * y_ratio + (1 - reveal) * height * 0.012)
            phrase_color = GOLD if "Story" in phrase else WHITE
            layer_draw.text((x, y), phrase, font=font, fill=(*phrase_color, alpha))
            frame = Image.alpha_composite(frame, layer)
    # A restrained travelling light opens the frame into the first property photograph.
    if t >= 5.0:
        sweep = min(1.0, (t - 5.0) / 1.0)
        x = round(width * (sweep * 1.28 - 0.14))
        flare = Image.new("RGBA", size, (0, 0, 0, 0))
        flare_draw = ImageDraw.Draw(flare)
        flare_draw.line((x, 0, x + round(width * 0.16), height), fill=(247, 238, 218, round(30 * math.sin(math.pi * sweep))), width=round(width * 0.09))
        frame = Image.alpha_composite(frame, flare)
    return frame.convert("RGB")


def _gradient_overlay(frame, size, *, strength=205, closing=False):
    width, height = size
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    # Bottom gradient supports lower thirds while leaving the image visible.
    base = int(height * (0.48 if closing else 0.54))
    for y in range(base, height):
        p = (y - base) / max(1, height - base)
        alpha = round(strength * p * p)
        draw.line((0, y, width, y), fill=(*NAVY, alpha))
    if closing:
        draw.rectangle((0, 0, width, height), fill=(*NAVY, 92))
    return Image.alpha_composite(frame.convert("RGBA"), overlay)


def _draw_card(frame, size, segment, event_t, property_name, location, price, contact, index, total):
    width, height = size
    image = _gradient_overlay(frame, size, closing=segment["kind"] == "closing")
    draw = ImageDraw.Draw(image)
    margin_x = round(width * 0.075)
    accent_x = margin_x
    y_base = round(height * 0.68)
    card_width = min(round(width * 0.60), round(width * 0.70))
    card_height = round(height * 0.19)
    # Entrance and exit motion is tied to the spoken sentence boundaries.
    entrance = min(1.0, event_t / 0.38)
    exit_amount = min(1.0, (1.0 - event_t) / 0.30)
    opacity = round(255 * min(entrance, exit_amount))
    slide = round((1.0 - entrance) * height * 0.035)
    top = y_base + slide
    panel = Image.new("RGBA", size, (0, 0, 0, 0))
    panel_draw = ImageDraw.Draw(panel)
    bounds = (margin_x, top, margin_x + card_width, top + card_height)
    panel_draw.rounded_rectangle(bounds, radius=round(height * 0.022), fill=(*CHARCOAL, min(224, opacity)))
    panel_draw.rounded_rectangle((margin_x, top + 1, margin_x + 8, top + card_height - 1), radius=4, fill=(*GOLD, opacity))
    image = Image.alpha_composite(image, panel)
    draw = ImageDraw.Draw(image)
    label_font = _font(max(18, round(height * 0.022)), bold=True)
    detail_font = _font(max(32, round(height * 0.052)), bold=True, serif=segment["kind"] == "opening")
    small_font = _font(max(18, round(height * 0.021)))
    badge_size = max(54, round(height * 0.088 * (0.82 + 0.18 * entrance)))
    badge_left = margin_x + round(width * 0.020)
    badge_top = top + round((card_height - badge_size) * 0.5)
    draw.ellipse((badge_left, badge_top, badge_left + badge_size, badge_top + badge_size),
                 outline=(*GOLD, opacity), width=max(2, round(height * 0.003)))
    count_match = re.search(r"\d+", segment["detail"] or "")
    badge_mark = str(round(int(count_match.group()) * min(1.0, entrance * 1.7))) if count_match else {
        "location": "L", "type": "H", "bedrooms": "B", "bathrooms": "B", "kitchen": "K",
        "price": "P", "closing": ">", "opening": "S", "feature": "F",
    }.get(segment["kind"], "F")
    mark_font = _font(max(22, round(height * (0.043 if count_match else 0.035))), bold=True)
    mark_box = draw.textbbox((0, 0), badge_mark, font=mark_font)
    draw.text((badge_left + (badge_size - (mark_box[2] - mark_box[0])) / 2,
               badge_top + (badge_size - (mark_box[3] - mark_box[1])) / 2 - mark_box[1]),
              badge_mark, font=mark_font, fill=(*GOLD, opacity))
    text_x = badge_left + badge_size + round(width * 0.025)
    label = segment["title"].upper()
    label_color = TEAL if segment["kind"] in ("location", "type") else GOLD
    draw.text((text_x, top + round(height * 0.024)), label, font=label_font, fill=(*label_color, opacity))
    detail = segment["detail"] or segment["text"]
    # Explicitly wrap at a safe width to keep 16:9 and vertical outputs legible.
    max_width = card_width - round(width * 0.05)
    words, lines, current = detail.split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=detail_font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    line_height = detail_font.size + round(height * 0.008)
    for line_no, line in enumerate(lines[:2]):
        draw.text((text_x, top + round(height * 0.061) + line_no * line_height), line,
                  font=detail_font, fill=(*WHITE, opacity), stroke_width=0)
    # Scene marker and elegant brand stamp stay secondary to the synchronized card.
    brand_font = _font(max(15, round(height * 0.017)), bold=True)
    draw.text((margin_x, round(height * 0.08)), "SAFAR   /   PROPERTY FILM", font=brand_font, fill=(*WHITE, 224))
    draw.text((width - margin_x - round(width * 0.075), round(height * 0.08)), f"{index + 1:02d} / {total:02d}", font=brand_font, fill=(*WHITE, 210))
    if segment["kind"] == "opening":
        location_font = _font(max(20, round(height * 0.025)))
        draw.text((text_x, top + round(height * 0.125)), location, font=location_font, fill=(*TEAL, opacity))
        if price:
            price_font = _font(max(18, round(height * 0.022)), bold=True)
            draw.text((width - margin_x - round(width * 0.24), top + round(height * 0.03)), price, font=price_font, fill=(*GOLD, opacity))
    return image.convert("RGB")


def render_scene(image_bytes, caption, property_name, location, price, index, total, contact, size=(1920, 1080), camera_t=0.5):
    canvas = _cover_crop(image_bytes, size)
    frame = _camera_frame(canvas, size, index, camera_t)
    segment = _sentence(caption, "PROPERTY HIGHLIGHT", caption, "feature")
    return _draw_card(frame, size, segment, 0.65, property_name, location, price, contact, index, total)


async def _synthesize_segment(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice=voice, rate="-3%", pitch="-1Hz")
    await communicate.save(str(output_path))


def _synthesize_narration(segments, voice, work_dir):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    timeline, pcm_chunks = [], []
    current = 0.0
    sample_rate = 24000
    for index, segment in enumerate(segments):
        mp3_path = Path(work_dir) / f"speech-{index:02d}.mp3"
        wav_path = Path(work_dir) / f"speech-{index:02d}.wav"
        try:
            asyncio.run(asyncio.wait_for(_synthesize_segment(segment["text"], voice, mp3_path), timeout=45))
        except Exception as error:
            raise RuntimeError("Could not reach the online speech service. Check your internet connection, or turn off the voice cover.") from error
        result = subprocess.run([ffmpeg, "-y", "-v", "error", "-i", str(mp3_path), "-ac", "1", "-ar", str(sample_rate), "-sample_fmt", "s16", str(wav_path)], capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise RuntimeError("Could not prepare the generated male voice audio.")
        with wave.open(str(wav_path), "rb") as source:
            frames = source.readframes(source.getnframes())
            duration = source.getnframes() / source.getframerate()
        start = current
        end = start + duration
        timeline.append({**segment, "start": start, "end": end})
        pcm_chunks.append(frames)
        if index < len(segments) - 1:
            pause_frames = round(sample_rate * 0.23)
            pcm_chunks.append(b"\0\0" * pause_frames)
            current = end + pause_frames / sample_rate
        else:
            current = end
    voice_path = Path(work_dir) / "voice.wav"
    with wave.open(str(voice_path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(b"".join(pcm_chunks))
    return voice_path, timeline, current


def _mix_audio(voice_path, music_path, mixed_path, duration, ffmpeg, include_music):
    if include_music:
        audio_filter = f"[0:a]volume=0.08,afade=t=in:d=1.2,afade=t=out:st={max(0, duration - 1.8):.3f}:d=1.8[m];[1:a]volume=1.4,apad,atrim=0:{duration:.3f}[v];[m][v]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.92[out]"
        command = [ffmpeg, "-y", "-v", "error", "-i", str(music_path), "-i", str(voice_path), "-filter_complex", audio_filter, "-map", "[out]"]
    else:
        command = [ffmpeg, "-y", "-v", "error", "-i", str(voice_path), "-af", f"apad,atrim=0:{duration:.3f}"]
    result = subprocess.run(command + ["-t", f"{duration:.3f}", "-ac", "2", "-ar", "44100", str(mixed_path)], capture_output=True, text=True, timeout=120)
    if result.returncode or not Path(mixed_path).is_file():
        raise RuntimeError("Could not mix the voiceover and background music.")


def _prepare_music(music_path, output_path, duration, ffmpeg):
    fade_start = max(0, duration - 1.8)
    result = subprocess.run([ffmpeg, "-y", "-v", "error", "-i", str(music_path), "-af",
        f"volume=0.38,afade=t=in:d=1.2,afade=t=out:st={fade_start:.3f}:d=1.8", "-t", f"{duration:.3f}",
        "-ac", "2", "-ar", "44100", str(output_path)], capture_output=True, text=True, timeout=120)
    if result.returncode or not Path(output_path).is_file():
        raise RuntimeError("Could not prepare the background soundtrack.")


def _make_brand_audio(output_path, ffmpeg):
    """Create a six-second original, instrumental logo-reveal whoosh."""
    noise = "anoisesrc=color=pink:amplitude=0.10:sample_rate=44100:duration=6"
    tone = "sine=frequency=110:sample_rate=44100:duration=6"
    filters = (
        "[0:a]highpass=f=320,lowpass=f=2800,volume=0.35,"
        "afade=t=in:d=0.35,afade=t=out:st=5.25:d=0.75[n];"
        "[1:a]lowpass=f=420,volume=0.75,afade=t=in:d=1.0,afade=t=out:st=4.4:d=1.6[t];"
        "[n][t]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.82[out]"
    )
    result = subprocess.run([ffmpeg, "-y", "-v", "error", "-f", "lavfi", "-i", noise,
        "-f", "lavfi", "-i", tone, "-filter_complex", filters, "-map", "[out]", "-t", "6",
        "-ac", "2", "-ar", "44100", str(output_path)], capture_output=True, text=True, timeout=30)
    if result.returncode or not Path(output_path).is_file():
        raise RuntimeError(f"Could not create the SAFAR intro sound: {result.stderr.strip()}")


def _join_intro_and_property_audio(intro_path, property_path, output_path, ffmpeg):
    result = subprocess.run([ffmpeg, "-y", "-v", "error", "-i", str(intro_path), "-i", str(property_path),
        "-filter_complex", "[0:a]aformat=sample_rates=44100:channel_layouts=stereo[i];"
        "[1:a]aformat=sample_rates=44100:channel_layouts=stereo[p];[i][p]concat=n=2:v=0:a=1[out]",
        "-map", "[out]", "-ac", "2", "-ar", "44100", str(output_path)],
        capture_output=True, text=True, timeout=60)
    if result.returncode or not Path(output_path).is_file():
        raise RuntimeError("Could not join the SAFAR intro sound and property audio.")


def _event_at(timeline, timestamp):
    for index, event in enumerate(timeline):
        if event["start"] <= timestamp < event["end"]:
            return event, (timestamp - event["start"]) / max(0.01, event["end"] - event["start"])
        if index + 1 < len(timeline) and event["end"] <= timestamp < timeline[index + 1]["start"]:
            return event, 0.65
    if timeline and timestamp < timeline[0]["start"]:
        return timeline[0], 0.0
    if timeline and timestamp >= timeline[-1]["end"]:
        return timeline[-1], 1.0
    return None, 0.0


def _estimate_timeline(segments, words_per_minute=165):
    """Approximate speech timing for an explicitly unvoiced visual-only preview."""
    timeline = []
    current = 0.0
    for index, segment in enumerate(segments):
        duration = max(0.9, len(segment["text"].split()) * 60 / words_per_minute)
        timeline.append({**segment, "start": current, "end": current + duration})
        current += duration + (0.23 if index < len(segments) - 1 else 0)
    return timeline, current


def generate_video(images, captions, property_name, location, price="", contact="", *, output_path=None, vertical=False, seconds_per_scene=5.0, progress_callback=None, voiceover_text=None, voiceover_segments=None, voice="en-US-GuyNeural", include_music=True, resolution="1080p", synthesize_voice=True, include_brand_intro=True):
    if not images or len(images) != len(captions):
        raise ValueError("Each uploaded photo must have one caption.")
    if not include_music and not (voiceover_segments or voiceover_text):
        raise ValueError("Enable voiceover or background music so the exported video has audio.")
    short_side = 1080 if resolution == "1080p" else 720
    size = (short_side, round(short_side * 16 / 9)) if vertical else (round(short_side * 16 / 9), short_side)
    scratch_dir = Path(output_path).parent if output_path else Path(__file__).resolve().parents[1] / "output"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[1]
    soundtrack_path = root / "assets" / "safar_travel.mp3"
    if include_music and not soundtrack_path.is_file():
        raise RuntimeError("Safar's background soundtrack is missing. Restore assets/safar_travel.mp3 and try again.")
    if voiceover_segments is None and voiceover_text:
        voiceover_segments = [_sentence(voiceover_text, "PROPERTY FILM", property_name, "opening")]
    voiceover_segments = voiceover_segments or []
    with tempfile.TemporaryDirectory(prefix="safar-", dir=scratch_dir) as temp_dir:
        target = Path(output_path) if output_path else Path(temp_dir) / "property.mp4"
        target.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        timeline, voice_path = [], None
        speech_duration = 0.0
        if voiceover_segments and synthesize_voice:
            voice_path, timeline, speech_duration = _synthesize_narration(voiceover_segments, voice, temp_dir)
        elif voiceover_segments:
            timeline, speech_duration = _estimate_timeline(voiceover_segments)
        property_duration = min(34.0, max(14.0, speech_duration + 2.4)) if speech_duration else len(images) * seconds_per_scene
        if speech_duration > property_duration - 1.5:
            property_duration = min(34.0, speech_duration + 1.5)
        property_audio_path = None
        if voice_path:
            property_audio_path = Path(temp_dir) / "property-mix.wav"
            _mix_audio(voice_path, soundtrack_path, property_audio_path, property_duration, ffmpeg, include_music)
        elif include_music:
            property_audio_path = Path(temp_dir) / "property-music.wav"
            _prepare_music(soundtrack_path, property_audio_path, property_duration, ffmpeg)
        intro_frames = BRAND_INTRO_FRAMES if include_brand_intro else 0
        intro_seconds = BRAND_INTRO_SECONDS if include_brand_intro else 0.0
        audio_path = property_audio_path
        if include_brand_intro:
            intro_audio = Path(temp_dir) / "safar-intro.wav"
            _make_brand_audio(intro_audio, ffmpeg)
            if property_audio_path:
                audio_path = Path(temp_dir) / "complete-audio.wav"
                _join_intro_and_property_audio(intro_audio, property_audio_path, audio_path, ffmpeg)
            else:
                audio_path = intro_audio
        frames_per_scene = round(property_duration * FPS / len(images))
        frame_count = frames_per_scene * len(images)
        property_video_duration = frame_count / FPS
        total_frame_count = intro_frames + frame_count
        video_duration = intro_seconds + property_video_duration
        encoder_kwargs = {"audio_path": str(audio_path), "audio_codec": "aac"} if audio_path else {}
        encoder = imageio_ffmpeg.write_frames(
            str(target), size, fps=FPS, codec="libx264", quality=8, macro_block_size=1, ffmpeg_log_level="error",
            output_params=["-preset", "ultrafast", "-movflags", "+faststart", "-pix_fmt", "yuv420p", "-t", f"{video_duration:.4f}"],
            **encoder_kwargs,
        )
        try:
            encoder.send(None)
            previous_scene_end = None
            last_scene_index = -1
            dissolve_frames = 16
            canvases = [_cover_crop(photo, size) for photo in images]
            first_property = _camera_frame(canvases[0], size, 0, 0.0)
            for intro_index in range(intro_frames):
                intro_frame = _brand_intro_frame(size, intro_index)
                transition_at = intro_frames - round(0.5 * FPS)
                if intro_index >= transition_at:
                    amount = (intro_index - transition_at + 1) / max(1, intro_frames - transition_at)
                    intro_frame = Image.blend(intro_frame, first_property, min(1.0, amount))
                encoder.send(np.asarray(intro_frame, dtype=np.uint8).tobytes())
                if progress_callback and intro_index % FPS == 0:
                    progress_callback(intro_index + 1, total_frame_count)
            for frame_index in range(frame_count):
                timestamp = frame_index / FPS
                scene_float = timestamp / property_video_duration * len(images)
                scene_index = min(len(images) - 1, int(scene_float))
                scene_t = scene_float - scene_index
                frame = _camera_frame(canvases[scene_index], size, scene_index, scene_t)
                event, event_t = _event_at(timeline, timestamp) if timeline else (None, 0.0)
                if event is None:
                    event = _sentence("", "PROPERTY FILM", property_name, "opening" if timestamp < 3 else "feature")
                    event_t = 1.0
                if timeline and timestamp >= timeline[-1]["end"]:
                    event = timeline[-1]
                    event_t = 0.65
                if timestamp >= video_duration - 2.3 and timeline:
                    event = timeline[-1]
                    event_t = 0.65
                frame = _draw_card(frame, size, event, event_t, property_name, location, price, contact, scene_index, len(images))
                if previous_scene_end is not None and scene_t * frames_per_scene < dissolve_frames:
                    amount = (scene_t * frames_per_scene + 1) / dissolve_frames
                    frame = Image.blend(previous_scene_end, frame, min(1.0, amount))
                if scene_index != last_scene_index:
                    last_scene_index = scene_index
                if scene_t >= 1.0 - 1 / frames_per_scene:
                    previous_scene_end = frame.copy()
                encoder.send(np.asarray(frame, dtype=np.uint8).tobytes())
                if progress_callback and (frame_index % 30 == 0 or frame_index == frame_count - 1):
                    progress_callback(intro_frames + frame_index + 1, total_frame_count)
        finally:
            encoder.close()
        data = target.read_bytes()
        if b"ftyp" not in data[:32] or len(data) < 2048:
            raise RuntimeError("The encoder did not produce a valid MP4 file.")
        return data
