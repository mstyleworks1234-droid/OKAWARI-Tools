import io
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from imageport.convert import fit_max_edge, to_bytes
from imageport.errors import AnimatedGifError, UnsupportedFormatError
from imageport.formats import FUTURE_EXTENSIONS, INPUT_EXTENSIONS, input_kind
from imageport.load import load_image
from imageport.pipeline import convert_file
from imageport.save import NameAllocator
from imageport.settings import load_settings, save_settings


def _png(path: Path, size=(40, 20), color=(255, 0, 0, 255)) -> None:
    Image.new("RGBA", size, color).save(path, format="PNG")


class FormatTests(unittest.TestCase):
    def test_supported_and_future_formats_stay_separate(self):
        self.assertIn(".webp", INPUT_EXTENSIONS)
        self.assertNotIn(".heic", INPUT_EXTENSIONS)
        for suffix in (".heic", ".heif", ".avif", ".svg"):
            self.assertIn(suffix, FUTURE_EXTENSIONS)
            self.assertEqual(input_kind(suffix), "future")


class ConvertTests(unittest.TestCase):
    def test_resize_does_not_enlarge(self):
        image = Image.new("RGB", (100, 40), "blue")
        self.assertEqual(fit_max_edge(image, 800).size, (100, 40))
        self.assertEqual(fit_max_edge(image, 50).size, (50, 20))

    def test_auto_uses_jpeg_without_alpha_and_webp_with_alpha(self):
        opaque = Image.new("RGB", (30, 30), "green")
        _, ext = to_bytes(opaque, "auto", None)
        self.assertEqual(ext, ".jpg")
        transparent = Image.new("RGBA", (30, 30), (1, 2, 3, 0))
        data, ext = to_bytes(transparent, "auto", None)
        self.assertEqual(ext, ".webp")
        self.assertTrue(data.startswith(b"RIFF"))

    def test_explicit_png_and_ico(self):
        image = Image.new("RGB", (400, 100), "red")
        data, ext = to_bytes(image, "png", 800)
        self.assertEqual(ext, ".png")
        self.assertEqual(Image.open(io.BytesIO(data)).size, (400, 100))
        data, ext = to_bytes(image, "ico", None)
        self.assertEqual(ext, ".ico")
        self.assertLessEqual(max(Image.open(io.BytesIO(data)).size), 256)


class PipelineTests(unittest.TestCase):
    def test_writes_copy_and_keeps_source(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "写真.png"
            _png(source)
            original = source.read_bytes()
            result = convert_file(source, "jpeg", None, NameAllocator())
            self.assertEqual(source.read_bytes(), original)
            self.assertTrue(result.output.exists())
            self.assertEqual(result.output.parent.name, "ImagePort")
            self.assertNotEqual(result.output.resolve(), source.resolve())
            self.assertGreater(result.before, 0)
            self.assertEqual(result.after, result.output.stat().st_size)

    def test_same_name_gets_a_number(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "photo.png"
            _png(source)
            names = NameAllocator()
            first = convert_file(source, "png", None, names)
            second = convert_file(source, "png", None, names)
            self.assertEqual(first.output.name, "photo.png")
            self.assertEqual(second.output.name, "photo_2.png")
            self.assertTrue(source.exists())

    def test_animated_gif_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "move.gif"
            frame_a = Image.new("RGB", (8, 8), "red")
            frame_b = Image.new("RGB", (8, 8), "blue")
            frame_a.save(source, save_all=True, append_images=[frame_b], duration=100, loop=0)
            with self.assertRaises(AnimatedGifError):
                load_image(source)

    def test_still_gif_can_be_converted(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "still.gif"
            Image.new("RGB", (8, 8), "red").save(source, format="GIF")
            result = convert_file(source, "png", None, NameAllocator())
            self.assertEqual(result.output.suffix, ".png")

    def test_future_format_is_not_opened(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "photo.heic"
            source.write_bytes(b"not an image")
            with self.assertRaises(UnsupportedFormatError):
                load_image(source)


class SettingsTests(unittest.TestCase):
    def test_roundtrip_and_unknown_values(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "settings.json"
            save_settings({"output_format": "webp", "resize": "1280"}, path)
            loaded = load_settings(path)
            self.assertEqual(loaded["settings_version"], 1)
            self.assertEqual(loaded["output_format"], "webp")
            self.assertEqual(loaded["resize"], "1280")
            path.write_text(json.dumps({"output_format": "avif", "resize": "10", "extra": 1}), encoding="utf-8")
            loaded = load_settings(path)
            self.assertEqual(loaded["output_format"], "auto")
            self.assertEqual(loaded["resize"], "none")
            path.write_text("{", encoding="utf-8")
            self.assertEqual(load_settings(path)["output_format"], "auto")


if __name__ == "__main__":
    unittest.main()
