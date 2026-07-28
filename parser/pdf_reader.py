"""PDF reader with OCR fallback for scanned pages."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

import fitz
from PIL import Image

from parser.image_reader import _ocr_image


def read_pdf(file_path: str | Path) -> str:
    """Extract text from a PDF and OCR only pages without usable text."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF file not found: {path}")

    try:
        pages: list[str] = []
        with fitz.open(path) as document:
            for page in document:
                text = page.get_text("text").strip()
                if not text:
                    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                    image = Image.open(BytesIO(pixmap.tobytes("png")))
                    text = _ocr_image(image)
                if text:
                    pages.append(text)
        return "\n\n".join(pages).strip()
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Unable to read PDF: {path}") from exc
