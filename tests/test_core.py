import io
import tempfile
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageChops, ImageDraw
import imageio_ffmpeg

from src.script_generator import generate_captions
from src.validation import validate_image, validate_property
from src.video_generator import _brand_intro_frame, _event_at, build_voice_segments, generate_video, render_scene


def photo_bytes(color):
    image = Image.new("RGB", (320, 200), color)
    output = io.BytesIO()
    image.save(output, format="JPEG")
    return output.getvalue()


class ValidationTests(unittest.TestCase):
    def test_accepts_four_six_and_eight_images(self):
        for count in (4, 6, 8):
            self.assertEqual(validate_property("Fern House", "Pune", count), [])

    def test_required_fields_and_image_count(self):
        errors = validate_property("", "", 3)
        self.assertEqual(len(errors), 3)

    def test_validates_contents_not_only_extension(self):
        self.assertEqual(validate_image(photo_bytes("#226655"), "room.jpg"), (True, None))
        valid, error = validate_image(b"not an image", "fake.jpg")
        self.assertFalse(valid)
        self.assertIn("not a valid image", error)

    def test_rejects_unsupported_image_format(self):
        data = io.BytesIO()
        Image.new("RGB", (10, 10), "red").save(data, format="BMP")
        valid, error = validate_image(data.getvalue(), "photo.bmp")
        self.assertFalse(valid)
        self.assertIn("JPG, PNG, or WEBP", error)


class CaptionTests(unittest.TestCase):
    def test_offline_captions_use_only_supplied_facts(self):
        captions, source = generate_captions("Fern House", "Pune", "₹1 crore", "Villa", ["Private garden"], "Call Maya", 4, api_key="")
        self.assertEqual(len(captions), 4)
        self.assertEqual(source, "Built-in templates")
        self.assertTrue(any("Private garden" in item for item in captions))
        self.assertFalse(any("pool" in item.lower() or "near metro" in item.lower() for item in captions))

    def test_api_error_falls_back_without_exposing_error(self):
        with patch("groq.Groq", side_effect=RuntimeError("simulated provider outage")):
            captions, source = generate_captions("Fern House", "Pune", "", "Villa", [], "", 4, api_key="test-key", model="test-model")
        self.assertEqual(len(captions), 4)
        self.assertIn("Built-in templates", source)

    def test_ai_response_is_parsed_as_scene_captions(self):
        completion = type("Completion", (), {"choices": [type("Choice", (), {"message": type("Message", (), {"content": '{"captions":["Meet Fern House","At home in Pune","Private garden","Call Maya"]}'})()})()]})()
        client = type("Client", (), {"chat": type("Chat", (), {"completions": type("Completions", (), {"create": lambda *args, **kwargs: completion})()})()})()
        with patch("groq.Groq", return_value=client):
            captions, source = generate_captions("Fern House", "Pune", "", "Villa", ["Private garden"], "Call Maya", 4, api_key="test-key", model="test-model")
        self.assertEqual(captions, ["Meet Fern House", "At home in Pune", "Private garden", "Call Maya"])
        self.assertEqual(source, "Groq · test-model")


class VoiceScriptTests(unittest.TestCase):
    def test_script_segments_speak_only_supplied_facts_and_pair_each_card(self):
        segments = build_voice_segments(
            "Fern House", "Baner, Pune", "Independent house", "₹1.25 crore",
            ["2 BHK", "Modern kitchen"], "Call Maya at 90000 12345",
        )
        speech = " ".join(segment["text"] for segment in segments)
        self.assertIn("2 BHK", speech)
        self.assertIn("modern kitchen", speech)
        self.assertNotIn("pool", speech.lower())
        self.assertEqual([segment["title"] for segment in segments if segment["kind"] == "feature"], ["BEDROOMS", "KITCHEN"])
        self.assertEqual(segments[-1]["kind"], "closing")

    def test_sentence_pause_keeps_the_matching_card_visible(self):
        timeline = [
            {"text": "Located in Baner.", "title": "LOCATION", "detail": "Baner", "kind": "location", "start": 0.0, "end": 1.2},
            {"text": "A key feature is a garden.", "title": "FEATURE", "detail": "A garden", "kind": "feature", "start": 1.4, "end": 2.5},
        ]
        event, event_t = _event_at(timeline, 1.3)
        self.assertEqual(event["title"], "LOCATION")
        self.assertGreater(event_t, 0.6)


class VideoTests(unittest.TestCase):
    def test_brand_intro_frames_render_in_sequence(self):
        opening = _brand_intro_frame((640, 360), 0)
        reveal = _brand_intro_frame((640, 360), 75)
        transition = _brand_intro_frame((640, 360), 179)
        self.assertEqual(opening.size, (640, 360))
        self.assertIsNotNone(ImageChops.difference(opening, reveal).getbbox())
        self.assertIsNotNone(ImageChops.difference(reveal, transition).getbbox())

    def test_virtual_camera_changes_the_frame(self):
        image = Image.new("RGB", (320, 200), "#36766c")
        draw = ImageDraw.Draw(image)
        draw.rectangle((12, 18, 95, 180), fill="#f2d48c")
        draw.rectangle((210, 25, 305, 160), fill="#283d35")
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        photo = buffer.getvalue()
        start = render_scene(photo, "Private garden", "Fern House", "Pune", "", 0, 4, "", camera_t=0)
        end = render_scene(photo, "Private garden", "Fern House", "Pune", "", 0, 4, "", camera_t=1)
        self.assertIsNotNone(ImageChops.difference(start, end).getbbox())

    def test_renders_decodable_mp4_in_both_formats(self):
        photos = [photo_bytes(color) for color in ("#36766c", "#758e7b", "#526b68", "#9a8068")]
        cases = ((4, False), (6, False), (8, False), (4, True))
        for count, vertical in cases:
            with self.subTest(count=count, vertical=vertical), tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1] / "output") as directory:
                path = Path(directory) / "sample.mp4"
                scene_photos = (photos * 2)[:count]
                captions = [f"Verified demo scene {index + 1}" for index in range(count)]
                data = generate_video(scene_photos, captions, "Fern House", "Pune", "₹1 crore", "Call Maya", output_path=path, vertical=vertical, seconds_per_scene=0.15, resolution="720p", include_brand_intro=False)
                self.assertGreater(len(data), 2048)
                self.assertIn(b"ftyp", data[:32])
                self.assertTrue(path.exists())
                result = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", str(path), "-f", "null", "NUL"], capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                audio = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", str(path), "-map", "0:a:0", "-f", "null", "NUL"], capture_output=True, text=True, timeout=30)
                self.assertEqual(audio.returncode, 0, audio.stderr)


if __name__ == "__main__":
    unittest.main()
