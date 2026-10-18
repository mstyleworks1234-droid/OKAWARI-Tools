from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

from imageport.errors import AnimatedGifError, UnsupportedFormatError
from imageport.formats import input_kind


def load_image(path: Path) -> Image.Image:
    kind = input_kind(path.suffix)
    if kind == "future":
        raise UnsupportedFormatError("この形式は現在のバージョンでは未対応です")
    if kind != "supported":
        raise UnsupportedFormatError("未対応の形式です")
    try:
        image = Image.open(path)
        image.load()
    except UnsupportedFormatError:
        raise
    except Exception as exc:
        raise UnsupportedFormatError("画像を開けませんでした") from exc
    if image.format == "GIF" and getattr(image, "n_frames", 1) > 1:
        image.close()
        raise AnimatedGifError("アニメーションGIFは変換しません")
    try:
        oriented = ImageOps.exif_transpose(image)
    except Exception:
        oriented = image
    if oriented is not image:
        image.close()
    return oriented
