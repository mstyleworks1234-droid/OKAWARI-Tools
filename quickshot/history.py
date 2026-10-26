"""Recent capture list. Removing an entry does not delete the image."""

import json
import os
import time

import imageutil


def _dir():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    folder = os.path.join(base, "OKAWARI", "QuickShot")
    os.makedirs(folder, exist_ok=True)
    return folder


def _path():
    return os.path.join(_dir(), "history.json")


def _thumbs():
    folder = os.path.join(_dir(), "thumbs")
    os.makedirs(folder, exist_ok=True)
    return folder


def load():
    try:
        with open(_path(), encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict) and item.get("path")]
    except Exception:
        pass
    return []


def _save(items):
    path = _path()
    temp = path + ".tmp"
    with open(temp, "w", encoding="utf-8") as handle:
        json.dump(items[:100], handle, ensure_ascii=False)
    os.replace(temp, path)


def add(path):
    if not path or not os.path.isfile(path):
        return
    width, height = imageutil.dimensions(path)
    stamp = int(time.time() * 1000)
    thumb = os.path.join(_thumbs(), "%d.png" % stamp)
    try:
        imageutil.thumbnail(path, thumb)
    except Exception:
        thumb = ""
    items = [item for item in load() if os.path.abspath(item.get("path", "")) != os.path.abspath(path)]
    items.insert(0, {
        "path": os.path.abspath(path),
        "time": time.time(),
        "w": width,
        "h": height,
        "bytes": os.path.getsize(path),
        "thumb": thumb,
    })
    _save(items)


def forget(path):
    target = os.path.abspath(path)
    _save([item for item in load() if os.path.abspath(item.get("path", "")) != target])
