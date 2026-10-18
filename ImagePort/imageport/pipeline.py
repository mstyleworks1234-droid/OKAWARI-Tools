from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from imageport.convert import to_bytes
from imageport.errors import ImagePortError
from imageport.load import load_image
from imageport.save import NameAllocator, write_new_file


@dataclass
class Converted:
    source: Path
    output: Path
    before: int
    after: int


@dataclass
class Failed:
    source: Path
    message: str


def convert_file(
    path: Path,
    output_format: str,
    max_edge: int | None,
    names: NameAllocator,
) -> Converted:
    source = Path(path)
    before = source.stat().st_size
    image = load_image(source)
    try:
        data, extension = to_bytes(image, output_format, max_edge)
    finally:
        image.close()
    destination = names.allocate(source, extension)
    try:
        write_new_file(destination, data)
    except FileExistsError:
        destination = names.allocate(source, extension)
        write_new_file(destination, data)
    except OSError as exc:
        raise ImagePortError("保存に失敗しました") from exc
    if destination.resolve() == source.resolve():
        raise ImagePortError("元画像と同じ場所には保存しません")
    return Converted(source, destination, before, destination.stat().st_size)
