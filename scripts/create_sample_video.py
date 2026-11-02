"""Create a clearly fictional, illustrated sample MP4 for local demonstration."""

import io
import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.script_generator import generate_captions
from src.video_generator import build_voice_segments, generate_video

parser = argparse.ArgumentParser(description="Create Safar's illustrated sample property film.")
parser.add_argument("--visual-only", action="store_true", help="Render an unvoiced preview when online TTS access is unavailable.")
args = parser.parse_args()
sample = json.loads((ROOT / "src/sample_data/property.json").read_text(encoding="utf-8"))


def illustrated_scene(index):
    palettes = [
        ("#dcebe5", "#7da99b", "#204a42"),
        ("#e9e3cf", "#94a97d", "#53664a"),
        ("#e5ecea", "#98b4ad", "#54736a"),
        ("#e9e2d9", "#b6a48d", "#655849"),
    ]
    sky, mid, dark = palettes[index % len(palettes)]
    image = Image.new("RGB", (1280, 720), sky)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 470, 1280, 720), fill=mid)
    draw.ellipse((930, 85, 1080, 235), fill="#f3d995")
    draw.polygon([(0, 455), (260, 270), (520, 450)], fill="#72988d")
    draw.polygon([(390, 455), (760, 220), (1110, 455)], fill="#88a99b")
    # Simple original illustration elements vary by scene, not generated property photos.
    if index == 0:
        draw.rectangle((340, 330, 900, 560), fill="#f2eee4")
        draw.polygon([(300, 345), (620, 150), (945, 345)], fill="#52685f")
        draw.rectangle((410, 385, 520, 505), fill="#8aa9a1")
        draw.rectangle((720, 380, 815, 560), fill="#8d755e")
    elif index == 1:
        for x, y in ((180, 365), (1030, 345), (1120, 410)):
            draw.rectangle((x + 29, y + 50, x + 43, y + 155), fill="#695b48")
            draw.ellipse((x, y - 25, x + 75, y + 60), fill="#466b51")
        draw.rectangle((460, 390, 820, 540), fill="#e5dccb")
        draw.polygon([(430, 400), (640, 265), (850, 400)], fill="#806f5d")
    elif index == 2:
        draw.rectangle((255, 280, 1000, 570), fill="#efe9df")
        draw.rectangle((355, 330, 555, 475), fill="#82aaa6")
        draw.rectangle((725, 330, 900, 480), fill="#82aaa6")
        draw.rectangle((350, 495, 875, 560), fill="#9f8871")
        draw.rectangle((430, 425, 800, 515), fill="#526c64")
    else:
        draw.rectangle((260, 285, 1015, 570), fill="#f0e8db")
        draw.rectangle((330, 350, 950, 445), fill="#aa9279")
        draw.rectangle((350, 325, 560, 440), fill="#e5ded2")
        draw.rectangle((690, 330, 935, 440), fill="#d2c3b0")
        draw.rectangle((425, 458, 840, 560), fill="#778b7f")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


photos = [illustrated_scene(i) for i in range(4)]
captions, _ = generate_captions(
    sample["property_name"], sample["location"], sample["price"],
    sample["property_type"], sample["features"], sample["contact"], 4,
    api_key="",
)
destination = ROOT / ("output/safar_visual_preview.mp4" if args.visual_only else "output/safar_sample.mp4")
voice_segments = build_voice_segments(
    sample["property_name"], sample["location"], sample["property_type"],
    sample["price"], sample["features"], sample["contact"],
)
generate_video(
    photos, captions, sample["property_name"], sample["location"],
    sample["price"], sample["contact"], output_path=destination,
    voiceover_segments=voice_segments, voice="en-US-GuyNeural", include_music=True,
    resolution="1080p", synthesize_voice=not args.visual_only,
)
print(f"Created {'visual-only preview' if args.visual_only else 'voiceover sample'}: {destination} ({destination.stat().st_size:,} bytes)")
