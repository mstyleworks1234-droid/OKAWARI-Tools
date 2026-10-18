"""PNG encoding for 24-bit bottom-up DIBs. Stdlib only."""

import os
import struct
import time
import zlib

import capture


def dib_to_png(dib):
    header_size, width, height, _planes, bit_count = struct.unpack_from("<IiiHH", dib, 0)
    if bit_count != 24 or width < 1 or height < 1 or header_size < 40:
        raise ValueError("unsupported dib")
    stride = ((width * 3 + 3) // 4) * 4
    pixels = memoryview(dib)[header_size:]
    raw = bytearray()
    for row in range(height - 1, -1, -1):
        raw.append(0)
        start = row * stride
        line = pixels[start:start + width * 3]
        rgb = bytearray(width * 3)
        for index in range(width):
            rgb[index * 3] = line[index * 3 + 2]
            rgb[index * 3 + 1] = line[index * 3 + 1]
            rgb[index * 3 + 2] = line[index * 3]
        raw.extend(rgb)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    compressed = zlib.compress(bytes(raw), 6)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", compressed) + chunk(b"IEND", b"")


def output_dir():
    home = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    folder = os.path.join(home, "Pictures", "QuickShot")
    os.makedirs(folder, exist_ok=True)
    return folder


def unique_png(kind):
    folder = output_dir()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = os.path.join(folder, f"QuickShot-{kind}-{stamp}.png")
    number = 2
    while os.path.exists(path):
        path = os.path.join(folder, f"QuickShot-{kind}-{stamp}_{number}.png")
        number += 1
    return path


def save_full_screen():
    x, y, width, height = capture.virtual_screen()
    count = len(capture.monitors())
    dib = capture.capture_region(x, y, width, height)
    path = unique_png("screen")
    with open(path, "wb") as handle:
        handle.write(dib_to_png(dib))
    return path, count, width, height
