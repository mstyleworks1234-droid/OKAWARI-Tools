"""PNG load, draw, and clipboard conversion through Windows GDI+. Stdlib only."""

import ctypes
from ctypes import wintypes
import os
import struct

import capture

gdiplus = ctypes.WinDLL("gdiplus.dll")
PixelFormat24bppRGB = 0x00021808
UnitPixel = 2
LockReadWrite = 3
_token = ctypes.c_size_t()
_ready = False


class _Startup(ctypes.Structure):
    _fields_ = [
        ("GdiplusVersion", ctypes.c_uint32),
        ("DebugEventCallback", ctypes.c_void_p),
        ("SuppressBackgroundThread", ctypes.c_int),
        ("SuppressExternalCodecs", ctypes.c_int),
    ]


class _Rect(ctypes.Structure):
    _fields_ = [
        ("X", ctypes.c_int),
        ("Y", ctypes.c_int),
        ("Width", ctypes.c_int),
        ("Height", ctypes.c_int),
    ]


class _RectF(ctypes.Structure):
    _fields_ = [
        ("X", ctypes.c_float),
        ("Y", ctypes.c_float),
        ("Width", ctypes.c_float),
        ("Height", ctypes.c_float),
    ]


class _PointF(ctypes.Structure):
    _fields_ = [("X", ctypes.c_float), ("Y", ctypes.c_float)]


class _BitmapData(ctypes.Structure):
    _fields_ = [
        ("Width", ctypes.c_uint),
        ("Height", ctypes.c_uint),
        ("Stride", ctypes.c_int),
        ("PixelFormat", ctypes.c_int),
        ("Scan0", ctypes.c_void_p),
        ("Reserved", ctypes.c_void_p),
    ]


class _Guid(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_uint32),
        ("Data2", ctypes.c_uint16),
        ("Data3", ctypes.c_uint16),
        ("Data4", ctypes.c_ubyte * 8),
    ]


def _guid(text):
    parts = text.split("-")
    value = _Guid()
    value.Data1 = int(parts[0], 16)
    value.Data2 = int(parts[1], 16)
    value.Data3 = int(parts[2], 16)
    tail = bytes.fromhex(parts[3] + parts[4])
    value.Data4 = (ctypes.c_ubyte * 8)(*tail)
    return value


_PNG = _guid("557CF406-1A04-11D3-9A73-0000F81EF32E")


def _bind():
    specs = {
        "GdiplusStartup": ([ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p, ctypes.c_void_p], ctypes.c_int),
        "GdipCreateBitmapFromFile": ([wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p)], ctypes.c_int),
        "GdipCreateBitmapFromScan0": ([ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)], ctypes.c_int),
        "GdipGetImageWidth": ([ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)], ctypes.c_int),
        "GdipGetImageHeight": ([ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)], ctypes.c_int),
        "GdipDisposeImage": ([ctypes.c_void_p], ctypes.c_int),
        "GdipGetImageGraphicsContext": ([ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)], ctypes.c_int),
        "GdipDeleteGraphics": ([ctypes.c_void_p], ctypes.c_int),
        "GdipDrawImageRectI": ([ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int], ctypes.c_int),
        "GdipSaveImageToFile": ([ctypes.c_void_p, wintypes.LPCWSTR, ctypes.POINTER(_Guid), ctypes.c_void_p], ctypes.c_int),
        "GdipCloneBitmapAreaI": ([ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)], ctypes.c_int),
        "GdipCreatePen1": ([ctypes.c_uint, ctypes.c_float, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)], ctypes.c_int),
        "GdipDeletePen": ([ctypes.c_void_p], ctypes.c_int),
        "GdipDrawRectangle": ([ctypes.c_void_p, ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float], ctypes.c_int),
        "GdipDrawLine": ([ctypes.c_void_p, ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float], ctypes.c_int),
        "GdipCreateSolidFill": ([ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p)], ctypes.c_int),
        "GdipDeleteBrush": ([ctypes.c_void_p], ctypes.c_int),
        "GdipFillPolygon": ([ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(_PointF), ctypes.c_int, ctypes.c_int], ctypes.c_int),
        "GdipCreateFontFamilyFromName": ([wintypes.LPCWSTR, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)], ctypes.c_int),
        "GdipDeleteFontFamily": ([ctypes.c_void_p], ctypes.c_int),
        "GdipCreateFont": ([ctypes.c_void_p, ctypes.c_float, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)], ctypes.c_int),
        "GdipDeleteFont": ([ctypes.c_void_p], ctypes.c_int),
        "GdipDrawString": ([ctypes.c_void_p, wintypes.LPCWSTR, ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(_RectF), ctypes.c_void_p, ctypes.c_void_p], ctypes.c_int),
        "GdipBitmapLockBits": ([ctypes.c_void_p, ctypes.POINTER(_Rect), ctypes.c_uint, ctypes.c_int, ctypes.POINTER(_BitmapData)], ctypes.c_int),
        "GdipBitmapUnlockBits": ([ctypes.c_void_p, ctypes.POINTER(_BitmapData)], ctypes.c_int),
        "GdipGraphicsClear": ([ctypes.c_void_p, ctypes.c_uint], ctypes.c_int),
        "GdipSetInterpolationMode": ([ctypes.c_void_p, ctypes.c_int], ctypes.c_int),
    }
    for name, (args, restype) in specs.items():
        func = getattr(gdiplus, name)
        func.argtypes = args
        func.restype = restype


_bind()


def startup():
    global _ready
    if _ready:
        return
    info = _Startup(1, None, 0, 0)
    status = gdiplus.GdiplusStartup(ctypes.byref(_token), ctypes.byref(info), None)
    if status != 0:
        raise OSError("GdiplusStartup failed (%s)" % status)
    _ready = True


def _check(status, name):
    if status != 0:
        raise OSError("%s failed (%s)" % (name, status))


def _size(image):
    width = ctypes.c_uint()
    height = ctypes.c_uint()
    _check(gdiplus.GdipGetImageWidth(image, ctypes.byref(width)), "width")
    _check(gdiplus.GdipGetImageHeight(image, ctypes.byref(height)), "height")
    return int(width.value), int(height.value)


def _load(path):
    startup()
    image = ctypes.c_void_p()
    _check(gdiplus.GdipCreateBitmapFromFile(os.path.abspath(path), ctypes.byref(image)), "open")
    return image


def _dispose(image):
    if image is not None and getattr(image, "value", None):
        gdiplus.GdipDisposeImage(image)
        image.value = None


def dimensions(path):
    image = _load(path)
    try:
        return _size(image)
    finally:
        _dispose(image)


def _blank(width, height):
    image = ctypes.c_void_p()
    _check(
        gdiplus.GdipCreateBitmapFromScan0(int(width), int(height), 0, PixelFormat24bppRGB, None, ctypes.byref(image)),
        "blank",
    )
    graphics = ctypes.c_void_p()
    _check(gdiplus.GdipGetImageGraphicsContext(image, ctypes.byref(graphics)), "graphics")
    gdiplus.GdipSetInterpolationMode(graphics, 7)
    gdiplus.GdipGraphicsClear(graphics, 0xFFFFFFFF)
    return image, graphics


def _close_graphics(graphics):
    if graphics:
        gdiplus.GdipDeleteGraphics(graphics)


def _save(image, path):
    folder = os.path.dirname(os.path.abspath(path))
    if folder:
        os.makedirs(folder, exist_ok=True)
    _check(gdiplus.GdipSaveImageToFile(image, os.path.abspath(path), ctypes.byref(_PNG), None), "save")


def _flatten(path, max_pixels):
    source = _load(path)
    try:
        width, height = _size(source)
        if width < 1 or height < 1:
            raise ValueError("empty image")
        if width * height > max_pixels:
            raise ValueError("image too large")
        image, graphics = _blank(width, height)
        try:
            _check(gdiplus.GdipDrawImageRectI(graphics, source, 0, 0, width, height), "draw")
        finally:
            _close_graphics(graphics)
        return image, width, height
    finally:
        _dispose(source)


def _dib_from_bitmap(image, width, height):
    rect = _Rect(0, 0, width, height)
    data = _BitmapData()
    _check(gdiplus.GdipBitmapLockBits(image, ctypes.byref(rect), LockReadWrite, PixelFormat24bppRGB, ctypes.byref(data)), "lock")
    try:
        stride = int(data.Stride)
        row_bytes = width * 3
        dib_stride = (row_bytes + 3) & ~3
        pixels = bytearray(dib_stride * height)
        source = data.Scan0
        if stride < 0:
            source = data.Scan0 + stride * (height - 1)
            stride = -stride
        for row in range(height):
            raw = ctypes.string_at(source + row * stride, row_bytes)
            pixels[(height - 1 - row) * dib_stride:(height - 1 - row) * dib_stride + row_bytes] = raw
        header = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0, len(pixels), 0, 0, 0, 0)
        return header + bytes(pixels)
    finally:
        gdiplus.GdipBitmapUnlockBits(image, ctypes.byref(data))


def copy_png_file(path):
    image, width, height = _flatten(path, 12000000)
    try:
        capture.copy_dib_to_clipboard(_dib_from_bitmap(image, width, height))
    finally:
        _dispose(image)


def thumbnail(path, dest, edge=160):
    source = _load(path)
    try:
        width, height = _size(source)
        scale = min(1.0, float(edge) / max(width, height, 1))
        thumb_w = max(1, int(width * scale))
        thumb_h = max(1, int(height * scale))
        image, graphics = _blank(thumb_w, thumb_h)
        try:
            _check(gdiplus.GdipDrawImageRectI(graphics, source, 0, 0, thumb_w, thumb_h), "thumb")
        finally:
            _close_graphics(graphics)
        try:
            _save(image, dest)
        finally:
            _dispose(image)
        return dest
    finally:
        _dispose(source)


def split_strips(path, folder, strip=1800, max_strips=8, max_width=3000):
    source = _load(path)
    paths = []
    try:
        width, height = _size(source)
        scale = 1.0
        if max_width and width > max_width:
            scale = float(max_width) / width
        draw_w = max(1, int(width * scale))
        draw_h = max(1, int(height * scale))
        top = 0
        index = 0
        while top < draw_h and index < max_strips:
            band = min(strip, draw_h - top)
            image, graphics = _blank(draw_w, band)
            try:
                _check(
                    gdiplus.GdipDrawImageRectI(
                        graphics, source,
                        0, -top, draw_w, draw_h,
                    ),
                    "strip",
                )
            finally:
                _close_graphics(graphics)
            dest = os.path.join(folder, "strip-%d.png" % index)
            try:
                _save(image, dest)
            finally:
                _dispose(image)
            paths.append(dest)
            top += band
            index += 1
        return paths, index * strip < draw_h
    finally:
        _dispose(source)


def _pen(color, width):
    pen = ctypes.c_void_p()
    _check(gdiplus.GdipCreatePen1(color, float(width), UnitPixel, ctypes.byref(pen)), "pen")
    return pen


def _brush(color):
    brush = ctypes.c_void_p()
    _check(gdiplus.GdipCreateSolidFill(color, ctypes.byref(brush)), "brush")
    return brush


def _mosaic(image, width, height, box, block):
    rect = _Rect(0, 0, width, height)
    data = _BitmapData()
    _check(gdiplus.GdipBitmapLockBits(image, ctypes.byref(rect), LockReadWrite, PixelFormat24bppRGB, ctypes.byref(data)), "lock")
    try:
        stride = int(data.Stride)
        if stride < 0:
            return
        x0 = max(0, min(width - 1, int(box[0])))
        y0 = max(0, min(height - 1, int(box[1])))
        x1 = max(x0 + 1, min(width, int(box[0] + box[2])))
        y1 = max(y0 + 1, min(height, int(box[1] + box[3])))
        step = max(4, int(block))
        base = data.Scan0
        for y in range(y0, y1, step):
            for x in range(x0, x1, step):
                bw = min(step, x1 - x)
                bh = min(step, y1 - y)
                total = [0, 0, 0]
                count = 0
                for row in range(y, y + bh, max(1, bh // 3)):
                    line = ctypes.string_at(base + row * stride + x * 3, bw * 3)
                    for col in range(0, bw * 3, 3):
                        total[0] += line[col]
                        total[1] += line[col + 1]
                        total[2] += line[col + 2]
                        count += 1
                if not count:
                    continue
                color = bytes(channel // count for channel in total)
                for row in range(y, y + bh):
                    dest = base + row * stride + x * 3
                    ctypes.memmove(dest, color * bw, bw * 3)
    finally:
        gdiplus.GdipBitmapUnlockBits(image, ctypes.byref(data))


def _draw_ops(image, graphics, width, height, ops, scale):
    pen = _pen(0xFFDC2626, max(2.0, 3.0 * scale))
    brush = _brush(0xFF111827)
    family = ctypes.c_void_p()
    font = ctypes.c_void_p()
    try:
        if gdiplus.GdipCreateFontFamilyFromName("Segoe UI", None, ctypes.byref(family)) == 0:
            gdiplus.GdipCreateFont(family, max(12.0, 28.0 * scale), 0, UnitPixel, ctypes.byref(font))
        for op in ops:
            kind = op.get("t")
            if kind == "rect":
                gdiplus.GdipDrawRectangle(
                    graphics, pen,
                    float(op["x"]) * scale, float(op["y"]) * scale,
                    float(op["w"]) * scale, float(op["h"]) * scale,
                )
            elif kind == "arrow":
                x1 = float(op["x1"]) * scale
                y1 = float(op["y1"]) * scale
                x2 = float(op["x2"]) * scale
                y2 = float(op["y2"]) * scale
                gdiplus.GdipDrawLine(graphics, pen, x1, y1, x2, y2)
                dx, dy = x2 - x1, y2 - y1
                length = max((dx * dx + dy * dy) ** 0.5, 1.0)
                ux, uy = dx / length, dy / length
                px, py = -uy, ux
                size = max(8.0, 14.0 * scale)
                points = (_PointF * 3)(
                    _PointF(x2, y2),
                    _PointF(x2 - ux * size + px * size * 0.45, y2 - uy * size + py * size * 0.45),
                    _PointF(x2 - ux * size - px * size * 0.45, y2 - uy * size - py * size * 0.45),
                )
                gdiplus.GdipFillPolygon(graphics, brush, points, 3, 0)
            elif kind == "text" and font and op.get("text"):
                layout = _RectF(float(op["x"]) * scale, float(op["y"]) * scale, max(40.0, width - float(op["x"]) * scale), 80.0 * max(scale, 0.4))
                gdiplus.GdipDrawString(graphics, str(op["text"]), -1, font, ctypes.byref(layout), None, brush)
            elif kind == "mosaic":
                _mosaic(image, width, height, (
                    float(op["x"]) * scale, float(op["y"]) * scale,
                    float(op["w"]) * scale, float(op["h"]) * scale,
                ), max(4, int(14 * scale)))
    finally:
        if font:
            gdiplus.GdipDeleteFont(font)
        if family:
            gdiplus.GdipDeleteFontFamily(family)
        gdiplus.GdipDeletePen(pen)
        gdiplus.GdipDeleteBrush(brush)


def render(path, ops, dest, max_edge=0):
    source = _load(path)
    try:
        width, height = _size(source)
        if width * height > 40000000:
            raise ValueError("image too large")
        crop = next((op for op in ops if op.get("t") == "crop"), None)
        origin_x = 0
        origin_y = 0
        if crop:
            origin_x = max(0, min(width - 1, int(crop["x"])))
            origin_y = max(0, min(height - 1, int(crop["y"])))
            crop_w = max(1, min(width - origin_x, int(crop["w"])))
            crop_h = max(1, min(height - origin_y, int(crop["h"])))
            clipped = ctypes.c_void_p()
            _check(
                gdiplus.GdipCloneBitmapAreaI(origin_x, origin_y, crop_w, crop_h, PixelFormat24bppRGB, source, ctypes.byref(clipped)),
                "crop",
            )
            _dispose(source)
            source = None
            source = clipped
            width, height = crop_w, crop_h
        scale = 1.0
        if max_edge and max(width, height) > max_edge:
            scale = float(max_edge) / max(width, height)
        out_w = max(1, int(round(width * scale)))
        out_h = max(1, int(round(height * scale)))
        image, graphics = _blank(out_w, out_h)
        try:
            _check(gdiplus.GdipDrawImageRectI(graphics, source, 0, 0, out_w, out_h), "preview")
            shifted = []
            for op in ops:
                if op.get("t") == "crop":
                    continue
                item = dict(op)
                for key in ("x", "x1", "x2"):
                    if key in item:
                        item[key] = float(item[key]) - origin_x
                for key in ("y", "y1", "y2"):
                    if key in item:
                        item[key] = float(item[key]) - origin_y
                shifted.append(item)
            _draw_ops(image, graphics, out_w, out_h, shifted, scale)
        finally:
            _close_graphics(graphics)
        try:
            _save(image, dest)
        finally:
            _dispose(image)
        return out_w, out_h, scale
    finally:
        if source:
            _dispose(source)
