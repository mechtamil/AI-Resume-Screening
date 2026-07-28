"""OCR-backed image reader for common resume and JD image formats."""
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageOps


SUPPORTED_OCR_LANGUAGES = os.getenv("RECRUITOS_OCR_LANGUAGES", "eng").strip() or "eng"
try:
    OCR_PAGE_SEGMENTATION_MODE = max(0, min(13, int(os.getenv("RECRUITOS_OCR_PSM", "3"))))
except ValueError:
    OCR_PAGE_SEGMENTATION_MODE = 3


def _ocr_image(image: Image.Image) -> str:
    """Extract text from one image through the installed Tesseract engine."""
    try:
        import pytesseract
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "Image OCR requires the pytesseract Python package."
        ) from exc

    prepared = ImageOps.exif_transpose(image).convert("RGB")
    try:
        return pytesseract.image_to_string(
            prepared,
            lang=SUPPORTED_OCR_LANGUAGES,
            config=f"--psm {OCR_PAGE_SEGMENTATION_MODE}",
        ).strip()
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError(
            "Image OCR requires the Tesseract runtime. Install tesseract-ocr "
            "locally or include it in Streamlit Cloud packages.txt."
        ) from exc
    except Exception as exc:
        raise RuntimeError("Unable to extract text from the image.") from exc


def read_image(file_path: str | Path) -> str:
    """Read PNG/JPEG/WEBP/TIFF input and return OCR text."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image file not found: {path}")

    try:
        with Image.open(path) as image:
            frames: list[str] = []
            frame_count = int(getattr(image, "n_frames", 1) or 1)
            for index in range(frame_count):
                if frame_count > 1:
                    image.seek(index)
                text = _ocr_image(image.copy())
                if text:
                    frames.append(text)
            return "\n\n".join(frames).strip()
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Unable to read image: {path}") from exc
