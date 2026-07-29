"""OCR-backed image reader for common resume and JD image formats."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

from config.settings import (
    OCR_LANGUAGES,
    OCR_PAGE_SEGMENTATION_MODE,
    TESSERACT_CMD,
)
from services.ocr_runtime import configure_pytesseract


def _ocr_image(image: Image.Image) -> str:
    """Extract text from one image through the configured Tesseract engine."""
    try:
        import pytesseract
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "Image OCR requires the pytesseract Python package."
        ) from exc

    prepared = ImageOps.exif_transpose(image).convert("RGB")
    try:
        configure_pytesseract(
            pytesseract,
            configured_command=TESSERACT_CMD,
        )
        return pytesseract.image_to_string(
            prepared,
            lang=OCR_LANGUAGES,
            config=f"--psm {OCR_PAGE_SEGMENTATION_MODE}",
        ).strip()
    except RuntimeError:
        raise
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError(
            "Image OCR requires the Tesseract runtime. Install it and expose "
            "'tesseract' on PATH, or configure RECRUITOS_TESSERACT_CMD."
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
