from __future__ import annotations

import io

from PIL import Image

from imageport.errors import ImagePortError
from imageport.formats import OUTPUT_FORMATS, choose_auto_format


def fit_max_edge(image: Image.Image, max_edge: int | None) -> Image.Image:
    if not max_edge:
        return image
    width, height = image.size
    long_edge = max(width, height)
    if long_edge <= max_edge:
        return image
    scale = max_edge / long_edge
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return image.resize(size, Image.Resampling.LANCZOS)


def _flatten_for_jpeg(image: Image.Image) -> Image.Image:
    if image.mode == "RGB":
        return image
    rgba = image.convert("RGBA")
    background = Image.new("RGB", rgba.size, (255, 255, 255))
    background.paste(rgba, mask=rgba.getchannel("A"))
    return background


def prepare(image: Image.Image, format_key: str, max_edge: int | None) -> tuple[Image.Image, str]:
    if format_key == "auto":
        format_key = choose_auto_format(image)
    if format_key not in OUTPUT_FORMATS:
        raise ImagePortError("出力形式が不正です")
    working = fit_max_edge(image, max_edge)
    if format_key == "ico":
        working = fit_max_edge(working, 256)
    spec = OUTPUT_FORMATS[format_key]
    if spec.pil_format == "JPEG":
        working = _flatten_for_jpeg(working)
    elif spec.pil_format == "GIF":
        working = working.convert("P", palette=Image.Palette.ADAPTIVE)
    elif spec.pil_format == "BMP":
        working = working.convert("RGB")
    elif spec.pil_format in ("PNG", "WEBP", "TIFF", "ICO"):
        if working.mode not in ("RGB", "RGBA"):
            working = working.convert("RGBA" if "A" in image.getbands() else "RGB")
    return working, format_key


def to_bytes(image: Image.Image, format_key: str, max_edge: int | None) -> tuple[bytes, str]:
    prepared, resolved = prepare(image, format_key, max_edge)
    spec = OUTPUT_FORMATS[resolved]
    buffer = io.BytesIO()
    try:
        if spec.pil_format == "ICO":
            prepared.save(buffer, format="ICO", sizes=[prepared.size])
        else:
            prepared.save(buffer, format=spec.pil_format, **spec.save_kwargs())
    except Exception as exc:
        raise ImagePortError("変換に失敗しました") from exc
    finally:
        if prepared is not image:
            prepared.close()
    return buffer.getvalue(), spec.extension
