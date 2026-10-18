"""Output formats. Add a new still-image format by extending OUTPUT_FORMATS
and INPUT_EXTENSIONS. HEIC, HEIF, AVIF, SVG, and RAW are intentionally absent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PIL import Image


@dataclass(frozen=True)
class FormatSpec:
    key: str
    label: str
    extension: str
    pil_format: str
    save_kwargs: Callable[[], dict]


def _jpeg():
    return {"quality": 82, "optimize": True, "progressive": True}


def _png():
    return {"optimize": True}


def _webp():
    return {"quality": 80, "method": 4}


def _tiff():
    return {"compression": "tiff_lzw"}


def _gif():
    return {"optimize": True}


def _plain():
    return {}


OUTPUT_FORMATS: dict[str, FormatSpec] = {
    "jpeg": FormatSpec("jpeg", "JPG", ".jpg", "JPEG", _jpeg),
    "png": FormatSpec("png", "PNG", ".png", "PNG", _png),
    "webp": FormatSpec("webp", "WebP", ".webp", "WEBP", _webp),
    "bmp": FormatSpec("bmp", "BMP", ".bmp", "BMP", _plain),
    "tiff": FormatSpec("tiff", "TIFF", ".tif", "TIFF", _tiff),
    "gif": FormatSpec("gif", "GIF（静止画）", ".gif", "GIF", _gif),
    "ico": FormatSpec("ico", "ICO", ".ico", "ICO", _plain),
}

INPUT_EXTENSIONS = {
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".png": "png",
    ".webp": "webp",
    ".bmp": "bmp",
    ".tif": "tiff",
    ".tiff": "tiff",
    ".gif": "gif",
    ".ico": "ico",
}

# Dropped on purpose for this version. Recognized only so the UI can say so.
FUTURE_EXTENSIONS = {
    ".heic",
    ".heif",
    ".avif",
    ".svg",
    ".raw",
    ".cr2",
    ".nef",
    ".arw",
    ".dng",
}


def input_kind(suffix: str) -> str:
    suffix = suffix.lower()
    if suffix in INPUT_EXTENSIONS:
        return "supported"
    if suffix in FUTURE_EXTENSIONS:
        return "future"
    return "unknown"


def choose_auto_format(image: Image.Image) -> str:
    if image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    ):
        return "webp"
    return "jpeg"
