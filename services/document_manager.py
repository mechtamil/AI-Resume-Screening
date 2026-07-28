"""Read supported documents and return a standardized processed-document contract."""
from __future__ import annotations

from pathlib import Path

from parser.docx_reader import read_docx
from parser.image_reader import read_image
from parser.pdf_reader import read_pdf
from parser.spreadsheet_reader import read_spreadsheet
from parser.txt_reader import read_txt
from services.extraction_service import ExtractionService


class DocumentManager:
    """Resolve common recruitment document formats through one interface."""

    READERS = {
        ".pdf": read_pdf,
        ".docx": read_docx,
        ".txt": read_txt,
        ".csv": read_spreadsheet,
        ".xlsx": read_spreadsheet,
        ".xls": read_spreadsheet,
        ".png": read_image,
        ".jpg": read_image,
        ".jpeg": read_image,
        ".webp": read_image,
        ".tif": read_image,
        ".tiff": read_image,
    }

    @classmethod
    def read_document(cls, file_path: str | Path) -> dict:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Document not found: {path}")

        extension = path.suffix.casefold()
        reader = cls.READERS.get(extension)
        if reader is None:
            supported = ", ".join(sorted(cls.READERS))
            raise ValueError(
                f"Unsupported file type: {extension or '<none>'}. "
                f"Supported types: {supported}."
            )

        raw_text = reader(path)
        if not str(raw_text or "").strip():
            raise ValueError(
                f"No readable text could be extracted from {path.name}. "
                "Use a clearer file or the RecruitOS Excel template."
            )

        processed = ExtractionService.preprocess_document(raw_text)
        processed.update(
            {
                "file_name": path.name,
                "file_type": extension,
                "file_path": str(path),
            }
        )
        return processed
