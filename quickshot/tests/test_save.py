import json
import struct
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import bridge
import capture
import ocr
import pngsave


def tiny_dib(width, height, blue, green, red):
    stride = ((width * 3 + 3) // 4) * 4
    header = struct.pack(
        "<IiiHHIIiiII",
        40, width, height, 1, 24, 0, stride * height, 0, 0, 0, 0,
    )
    rows = []
    for _row in range(height):
        pixel = bytes((blue, green, red)) * width
        rows.append(pixel + bytes(stride - width * 3))
    return header + b"".join(rows)


class PngTests(unittest.TestCase):
    def test_dib_becomes_png(self):
        png = pngsave.dib_to_png(tiny_dib(2, 2, 10, 20, 30))
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(struct.unpack(">II", png[16:24]), (2, 2))

    def test_region_capture_still_returns_dib(self):
        dib = capture.capture_region(0, 0, 8, 8)
        self.assertGreater(len(dib), 40)
        self.assertTrue(pngsave.dib_to_png(dib).startswith(b"\x89PNG\r\n\x1a\n"))


class OutputDirTests(unittest.TestCase):
    def test_custom_folder_is_used_until_cleared(self):
        folder = tempfile.mkdtemp()
        try:
            self.assertTrue(pngsave.set_output_dir(folder))
            self.assertEqual(pngsave.output_dir(), folder)
            pngsave.set_output_dir("")
            self.assertNotEqual(pngsave.output_dir(), folder)
        finally:
            pngsave.set_output_dir("")


class ScreenTests(unittest.TestCase):
    def test_full_screen_png_includes_monitor_count(self):
        original = pngsave.output_dir
        with tempfile.TemporaryDirectory() as temp:
            pngsave.output_dir = lambda: temp
            try:
                path, count, width, height = pngsave.save_full_screen()
                self.assertGreaterEqual(count, 1)
                self.assertGreater(width, 0)
                self.assertGreater(height, 0)
                with open(path, "rb") as handle:
                    self.assertTrue(handle.read(8).startswith(b"\x89PNG"))
            finally:
                pngsave.output_dir = original


class BridgeTests(unittest.TestCase):
    def test_web_origin_and_missing_token_are_rejected(self):
        item = bridge.Bridge()
        item.token = "secret"
        server = ThreadingHTTPServer(("127.0.0.1", 0), bridge._Handler)
        server.bridge = item
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        port = server.server_address[1]
        try:
            denied = urllib.request.Request(
                f"http://127.0.0.1:{port}/save",
                data=b"\x89PNG\r\n\x1a\nnot-really",
                method="POST",
                headers={"Origin": "https://example.com", "X-QuickShot-Token": "secret"},
            )
            with self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(denied, timeout=3)
            self.assertEqual(raised.exception.code, 403)

            missing = urllib.request.Request(
                f"http://127.0.0.1:{port}/save",
                data=b"\x89PNG\r\n\x1a\nnot-really",
                method="POST",
            )
            with self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(missing, timeout=3)
            self.assertEqual(raised.exception.code, 403)
        finally:
            server.shutdown()
            server.server_close()

    def test_report_command_reaches_every_polling_host(self):
        item = bridge.Bridge()
        item.token = "secret"
        item.request_report()
        server = ThreadingHTTPServer(("127.0.0.1", 0), bridge._Handler)
        server.bridge = item
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        port = server.server_address[1]

        def grab():
            request = urllib.request.Request(
                "http://127.0.0.1:%d/command" % port,
                headers={"X-QuickShot-Token": "secret"},
            )
            with urllib.request.urlopen(request, timeout=3) as response:
                return json.loads(response.read().decode("utf-8"))

        try:
            self.assertEqual(grab()["type"], "report")
            self.assertEqual(grab()["type"], "report")
            item.request_capture("page")
            self.assertEqual(grab()["mode"], "page")
        finally:
            server.shutdown()
            server.server_close()

    def test_token_accepts_png_for_local_save(self):
        item = bridge.Bridge()
        item.token = "secret"
        server = ThreadingHTTPServer(("127.0.0.1", 0), bridge._Handler)
        server.bridge = item
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        port = server.server_address[1]
        png = pngsave.dib_to_png(tiny_dib(1, 1, 1, 2, 3))
        try:
            request = urllib.request.Request(
                f"http://127.0.0.1:{port}/save",
                data=png,
                method="POST",
                headers={"X-QuickShot-Token": "secret", "Content-Type": "application/octet-stream"},
            )
            with urllib.request.urlopen(request, timeout=3) as response:
                self.assertEqual(response.status, 200)
            messages = item.take_messages()
            self.assertEqual(messages[0]["type"], "png")
            self.assertTrue(messages[0]["data"].startswith(b"\x89PNG"))
            self.assertNotIn("part", messages[0])
            numbered = urllib.request.Request(
                f"http://127.0.0.1:{port}/save",
                data=png,
                method="POST",
                headers={
                    "X-QuickShot-Token": "secret",
                    "Content-Type": "application/octet-stream",
                    "X-QuickShot-Part": "2",
                },
            )
            with urllib.request.urlopen(numbered, timeout=3) as response:
                self.assertEqual(response.status, 200)
            follow = item.take_messages()
            self.assertEqual(follow[0]["part"], 2)
        finally:
            server.shutdown()


class OcrOrderTests(unittest.TestCase):
    def test_cjk_keeps_words_together_and_latin_spaces(self):
        self.assertEqual(ocr.join_words(["ここ", "を", "クリック"]), "ここをクリック")
        self.assertEqual(ocr.join_words(["Quick", "Shot"]), "Quick Shot")
        self.assertEqual(ocr.join_words(["コピ", "ー"]), "コピー")

    def test_table_rows_are_read_left_to_right_when_the_engine_jumps_up(self):
        items = [
            {"t": "完了", "x": 300, "y": 10, "w": 40, "h": 20},
            {"t": "完了", "x": 300, "y": 50, "w": 40, "h": 20},
            {"t": "機能", "x": 10, "y": 10, "w": 40, "h": 20},
            {"t": "切り抜き", "x": 10, "y": 50, "w": 60, "h": 20},
        ]
        self.assertEqual(ocr.reading_order(items), "機能\t完了\n切り抜き\t完了")

    def test_a_normal_column_keeps_engine_order(self):
        items = [
            {"t": "QuickShot", "x": 10, "y": 10, "w": 80, "h": 20},
            {"t": "ここをクリック", "x": 10, "y": 40, "w": 120, "h": 20},
            {"t": "押して", "x": 400, "y": 10, "w": 50, "h": 20},
            {"t": "文章", "x": 400, "y": 40, "w": 40, "h": 20},
        ]
        text = ocr.reading_order(items)
        self.assertTrue(text.startswith("QuickShot"))
        self.assertIn("ここをクリック", text)
        self.assertLess(text.find("ここをクリック"), text.find("押して"))


class EditorToolTests(unittest.TestCase):
    def test_crop_and_mosaic_can_be_undone_without_replacing_the_original(self):
        import os
        import tkinter as tk

        import editor
        import imageutil

        folder = tempfile.mkdtemp()
        src = os.path.join(folder, "base.png")
        with open(src, "wb") as handle:
            handle.write(pngsave.dib_to_png(tiny_dib(80, 40, 20, 40, 60)))
        original = open(src, "rb").read()
        cropped = os.path.join(folder, "crop.png")
        imageutil.render(src, [{"t": "crop", "x": 0, "y": 0, "w": 30, "h": 16}], cropped, 0)
        self.assertEqual(imageutil.dimensions(cropped), (30, 16))
        mosaic = os.path.join(folder, "mosaic.png")
        imageutil.render(src, [{"t": "mosaic", "x": 4, "y": 4, "w": 24, "h": 12}], mosaic, 0)
        self.assertEqual(imageutil.dimensions(mosaic), (80, 40))
        undone = os.path.join(folder, "undo.png")
        imageutil.render(src, [], undone, 0)
        self.assertEqual(imageutil.dimensions(undone), imageutil.dimensions(src))
        with open(src, "rb") as handle:
            self.assertEqual(handle.read(), original)
        root = tk.Tk()
        root.withdraw()
        window = editor.open_editor(root, src, lambda key: key)
        values = []

        def walk(widget):
            if widget.winfo_class() == "Radiobutton":
                values.append(str(widget.cget("value")))
            for child in widget.winfo_children():
                walk(child)

        try:
            walk(window)
            self.assertEqual(values, ["crop", "mosaic"])
        finally:
            window.destroy()
            root.destroy()


if __name__ == "__main__":
    unittest.main()
