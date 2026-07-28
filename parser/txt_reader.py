"""Plain-text document reader."""
from __future__ import annotations

from pathlib import Path


def read_txt(file_path: str | Path) -> str:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Text file not found: {path}")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise RuntimeError(f"Unable to read text file: {path}") from exc
