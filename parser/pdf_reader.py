"""PDF text reader."""
from __future__ import annotations

from pathlib import Path

import fitz


def read_pdf(file_path: str | Path) -> str:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF file not found: {path}")
    try:
        with fitz.open(path) as document:
            return "\n".join(page.get_text() for page in document)
    except Exception as exc:
        raise RuntimeError(f"Unable to read PDF: {path}") from exc
