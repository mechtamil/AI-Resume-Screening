"""DOCX text reader."""
from __future__ import annotations

from pathlib import Path

from docx import Document


def read_docx(file_path: str | Path) -> str:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"DOCX file not found: {path}")
    try:
        document = Document(path)
        return "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())
    except Exception as exc:
        raise RuntimeError(f"Unable to read DOCX: {path}") from exc
