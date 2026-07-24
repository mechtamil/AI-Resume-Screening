"""Read supported documents and return a standardized processed-document contract."""
from __future__ import annotations

from pathlib import Path

from parser.docx_reader import read_docx
from parser.pdf_reader import read_pdf
from parser.txt_reader import read_txt
from services.extraction_service import ExtractionService


class DocumentManager:
    READERS = {".pdf": read_pdf, ".docx": read_docx, ".txt": read_txt}

    @classmethod
    def read_document(cls, file_path: str | Path) -> dict:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Document not found: {path}")
        extension = path.suffix.lower()
        reader = cls.READERS.get(extension)
        if reader is None:
            raise ValueError(f"Unsupported file type: {extension or '<none>'}")
        raw_text = reader(path)
        processed = ExtractionService.preprocess_document(raw_text)
        processed.update(
            {
                "file_name": path.name,
                "file_type": extension,
                "file_path": str(path),
            }
        )
        return processed
