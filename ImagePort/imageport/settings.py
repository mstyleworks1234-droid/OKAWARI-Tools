from __future__ import annotations

import json
import os
from pathlib import Path

SETTINGS_VERSION = 1
RESIZE_CHOICES = {"none": None, "1920": 1920, "1280": 1280, "800": 800}
FORMAT_CHOICES = {"auto", "jpeg", "png", "webp", "bmp", "tiff", "gif", "ico"}

DEFAULTS = {
    "settings_version": SETTINGS_VERSION,
    "output_format": "auto",
    "resize": "none",
}


def settings_path() -> Path:
    root = os.environ.get("APPDATA") or str(Path.home())
    return Path(root) / "ImagePort" / "settings.json"


def load_settings(path: Path | None = None) -> dict:
    path = path or settings_path()
    data = dict(DEFAULTS)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return data
    if not isinstance(raw, dict):
        return data
    if raw.get("output_format") in FORMAT_CHOICES:
        data["output_format"] = raw["output_format"]
    if raw.get("resize") in RESIZE_CHOICES:
        data["resize"] = raw["resize"]
    return data


def save_settings(values: dict, path: Path | None = None) -> None:
    path = path or settings_path()
    payload = dict(DEFAULTS)
    if values.get("output_format") in FORMAT_CHOICES:
        payload["output_format"] = values["output_format"]
    if values.get("resize") in RESIZE_CHOICES:
        payload["resize"] = values["resize"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
