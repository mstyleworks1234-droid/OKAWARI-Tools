from __future__ import annotations

from pathlib import Path


OUTPUT_DIR_NAME = "ImagePort"


class NameAllocator:
    def __init__(self) -> None:
        self.reserved: set[Path] = set()

    def allocate(self, source: Path, extension: str) -> Path:
        directory = source.parent / OUTPUT_DIR_NAME
        directory.mkdir(parents=True, exist_ok=True)
        source_resolved = source.resolve()
        number = 1
        while True:
            stem = source.stem if number == 1 else f"{source.stem}_{number}"
            candidate = directory / f"{stem}{extension}"
            number += 1
            try:
                resolved = candidate.resolve()
            except OSError:
                continue
            if resolved == source_resolved or resolved in self.reserved or candidate.exists():
                continue
            self.reserved.add(resolved)
            return candidate


def write_new_file(path: Path, data: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(data)
