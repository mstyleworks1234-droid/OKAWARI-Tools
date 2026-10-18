import ctypes
import tempfile
import unittest
from ctypes import wintypes
from pathlib import Path
from unittest.mock import patch

import tkinter as tk
from PIL import Image

from imageport.dropfiles import WM_DROPFILES, enable_file_drop
from imageport.ui import App

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = ctypes.c_void_p
kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.SendMessageW.restype = ctypes.c_ssize_t


class DROPFILES(ctypes.Structure):
    _fields_ = [
        ("pFiles", wintypes.DWORD),
        ("x", wintypes.LONG),
        ("y", wintypes.LONG),
        ("fNC", wintypes.BOOL),
        ("fWide", wintypes.BOOL),
    ]


def make_hdrop(paths: list[str]):
    encoded = ("\0".join(paths) + "\0\0").encode("utf-16-le")
    header = DROPFILES()
    header.pFiles = ctypes.sizeof(DROPFILES)
    header.fWide = True
    size = ctypes.sizeof(DROPFILES) + len(encoded)
    raw = ctypes.create_string_buffer(size)
    ctypes.memmove(raw, ctypes.byref(header), ctypes.sizeof(header))
    ctypes.memmove(ctypes.addressof(raw) + ctypes.sizeof(header), encoded, len(encoded))
    handle = kernel32.GlobalAlloc(0x0002, size)
    pointer = kernel32.GlobalLock(handle)
    ctypes.memmove(pointer, raw, size)
    kernel32.GlobalUnlock(handle)
    return handle


class DropAndPickTests(unittest.TestCase):
    def test_drop_and_file_button_add_jpg_png_webp(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            jpg, png, webp = folder / "red.jpg", folder / "blue.png", folder / "green.webp"
            Image.new("RGB", (12, 12), "red").save(jpg, quality=90)
            Image.new("RGBA", (12, 12), (0, 0, 255, 255)).save(png)
            Image.new("RGB", (12, 12), "green").save(webp, format="WEBP", quality=80)
            paths = [str(jpg), str(png), str(webp)]

            root = tk.Tk()
            root.withdraw()
            try:
                app = App(root)
                enable_file_drop(root)
                user32.SendMessageW(wintypes.HWND(root.winfo_id()), WM_DROPFILES, make_hdrop(paths), 0)
                app._poll()
                self.assertEqual([path.name for path in app.files], ["red.jpg", "blue.png", "green.webp"])

                app._clear()
                with patch("imageport.ui.filedialog.askopenfilenames", return_value=paths):
                    app._pick()
                self.assertEqual([path.name for path in app.files], ["red.jpg", "blue.png", "green.webp"])
            finally:
                root.destroy()


if __name__ == "__main__":
    unittest.main()
