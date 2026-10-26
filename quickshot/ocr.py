"""Local text recognition through Windows.Media.Ocr. No network and no API key."""

import os
import subprocess
import tempfile

import imageutil

_SCRIPT = r"""
param([string]$Path, [string]$OutPath)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]
$null = [Windows.Media.Ocr.OcrResult,Windows.Foundation,ContentType=WindowsRuntime]
$null = [Windows.Globalization.Language,Windows.Globalization,ContentType=WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq "AsTask" -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq "IAsyncOperation``1" })[0]
function Await($task, $type) {
  $method = $asTask.MakeGenericMethod($type)
  $net = $method.Invoke($null, @($task))
  $net.Wait(-1) | Out-Null
  $net.Result
}
function Read-Image($file) {
  $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
  $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
  Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
}
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($Path)) ([Windows.Storage.StorageFile])
$bitmap = Read-Image $file
$ja = New-Object Windows.Globalization.Language "ja"
$engine = $null
if ([Windows.Media.Ocr.OcrEngine]::IsLanguageSupported($ja)) {
  $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($ja)
}
if ($null -eq $engine) { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages() }
if ($null -eq $engine) { Write-Output "QS_OCR_UNAVAILABLE"; exit 0 }
$result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
$lines = New-Object System.Collections.Generic.List[string]
foreach ($line in $result.Lines) {
  foreach ($word in $line.Words) {
    $box = $word.BoundingRect
    [void]$lines.Add(("{0}`t{1}`t{2}`t{3}`t{4}" -f $word.Text, [int]$box.X, [int]$box.Y, [int]$box.Width, [int]$box.Height))
  }
}
$payload = [string]::Join("`n", $lines)
[System.IO.File]::WriteAllText($OutPath, $payload, [System.Text.UTF8Encoding]::new($false))
"""


def _cjk(char):
    code = ord(char)
    return (
        0x3040 <= code <= 0x30FF
        or 0x3400 <= code <= 0x9FFF
        or 0xFF66 <= code <= 0xFF9D
        or char in "ー々〆"
    )


def _glue(text, word):
    if not text:
        return False
    end = text[-1]
    start = word[0]
    if _cjk(end) and _cjk(start):
        return True
    if _cjk(end) and word in ("ー", "－", "-"):
        return True
    marks = "、。・，！？!?,."
    if _cjk(end) and start in marks:
        return True
    if end in marks and (_cjk(start) or start.isalnum()):
        return True
    return False


def join_words(words):
    text = ""
    for word in words:
        word = (word or "").strip()
        if not word:
            continue
        if _glue(text, word):
            text += word
        elif text:
            text += " " + word
        else:
            text = word
    return text


def _parse_words(raw):
    items = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) != 5:
            continue
        text, x, y, width, height = parts
        try:
            items.append({
                "t": text,
                "x": int(float(x)),
                "y": int(float(y)),
                "w": max(1, int(float(width))),
                "h": max(1, int(float(height))),
            })
        except ValueError:
            continue
    return items


def _rows(items):
    pending = sorted(items, key=lambda item: (item["y"], item["x"]))
    lines = []
    for item in pending:
        center = item["y"] + item["h"] / 2.0
        placed = False
        for line in lines:
            other = line[0]["y"] + line[0]["h"] / 2.0
            if abs(center - other) <= max(item["h"], line[0]["h"]) * 0.55:
                line.append(item)
                placed = True
                break
        if not placed:
            lines.append([item])
    lines.sort(key=lambda line: min(word["y"] for word in line))
    return lines


def reading_order(items):
    """Keep Windows line order unless a later word jumps back up the page."""
    if not items:
        return ""
    jumped = False
    last_y = items[0]["y"]
    last_x = items[0]["x"]
    for item in items[1:]:
        # The engine read a right-hand column before the left-hand one.
        if item["y"] + item["h"] < last_y - max(8, item["h"] * 0.4) and item["x"] + 40 < last_x:
            jumped = True
            break
        if item["y"] >= last_y:
            last_y = item["y"]
            last_x = item["x"]
    if jumped:
        lines = _rows(items)
    else:
        lines = []
        for item in items:
            center = item["y"] + item["h"] / 2.0
            if lines:
                other = lines[-1][0]["y"] + lines[-1][0]["h"] / 2.0
                if abs(center - other) <= max(item["h"], lines[-1][0]["h"]) * 0.55:
                    lines[-1].append(item)
                    continue
            lines.append([item])
    output = []
    for line in lines:
        line.sort(key=lambda word: word["x"])
        text = ""
        previous = None
        for word in line:
            piece = (word["t"] or "").strip()
            if not piece:
                continue
            gap = 0 if previous is None else word["x"] - (previous["x"] + previous["w"])
            if previous is None:
                text = piece
            elif gap > max(18, previous["h"] * 0.8):
                text += "\t" + piece
            elif _glue(text, piece):
                text += piece
            else:
                text += " " + piece
            previous = word
        if text:
            output.append(text)
    return "\n".join(output)


def _upscale(path):
    width, height = imageutil.dimensions(path)
    if max(width, height) > 1600 or width * height > 1500000:
        return path
    dest = path + ".x2.png"
    imageutil.startup()
    source = imageutil._load(path)
    try:
        image, graphics = imageutil._blank(width * 2, height * 2)
        try:
            imageutil._check(
                imageutil.gdiplus.GdipDrawImageRectI(graphics, source, 0, 0, width * 2, height * 2),
                "upscale",
            )
        finally:
            imageutil._close_graphics(graphics)
        try:
            imageutil._save(image, dest)
        finally:
            imageutil._dispose(image)
    finally:
        imageutil._dispose(source)
    return dest


def _run(path):
    folder = tempfile.mkdtemp(prefix="qsocr")
    script = os.path.join(folder, "ocr.ps1")
    output = os.path.join(folder, "out.txt")
    with open(script, "w", encoding="utf-8-sig") as handle:
        handle.write(_SCRIPT)
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script, path, output],
            capture_output=True,
            timeout=40,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or b"ocr failed").decode("utf-8", "replace")
            raise RuntimeError(detail.strip()[:500])
        if not os.path.isfile(output):
            raise RuntimeError("ocr produced no text")
        with open(output, encoding="utf-8-sig") as handle:
            raw = handle.read()
        if raw.strip() == "QS_OCR_UNAVAILABLE":
            return raw.strip()
        return reading_order(_parse_words(raw))
    finally:
        for name in (script, output):
            try:
                os.remove(name)
            except OSError:
                pass
        try:
            os.rmdir(folder)
        except OSError:
            pass
    return ""


def recognize(path):
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(path or "")
    folder = tempfile.mkdtemp(prefix="qsstrip")
    try:
        strips, truncated = imageutil.split_strips(path, folder, max_width=0)
        parts = []
        for strip in strips:
            prepared = _upscale(strip)
            try:
                text = _run(prepared)
            finally:
                if prepared != strip:
                    try:
                        os.remove(prepared)
                    except OSError:
                        pass
            if text == "QS_OCR_UNAVAILABLE":
                raise RuntimeError("QS_OCR_UNAVAILABLE")
            if text:
                parts.append(text)
        if truncated:
            parts.append("...")
        return "\n".join(parts).strip()
    finally:
        for name in os.listdir(folder):
            try:
                os.remove(os.path.join(folder, name))
            except OSError:
                pass
        try:
            os.rmdir(folder)
        except OSError:
            pass
