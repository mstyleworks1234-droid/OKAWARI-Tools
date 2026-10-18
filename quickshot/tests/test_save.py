import struct
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import bridge
import capture
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
        finally:
            server.shutdown()


if __name__ == "__main__":
    unittest.main()
