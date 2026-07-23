"""
============================================================
RecruitOS
Document Manager
Version : 0.7
Author  : Tamilvanan A

Description:
Reads any supported document, automatically selects
the correct reader, and preprocesses the extracted text.

Supported:
✓ PDF
✓ DOCX
✓ TXT
============================================================
"""

from pathlib import Path

from parser.pdf_reader import read_pdf
from parser.docx_reader import read_docx
from parser.txt_reader import read_txt

from services.extraction_service import ExtractionService


class DocumentManager:
    """
    Responsible for reading any supported document and
    returning a standardized processed document.
    """

    @staticmethod
    def read_document(file_path: str) -> dict:

        extension = Path(file_path).suffix.lower()

        if extension == ".pdf":
            raw_text = read_pdf(file_path)

        elif extension == ".docx":
            raw_text = read_docx(file_path)

        elif extension == ".txt":
            raw_text = read_txt(file_path)

        else:
            raise ValueError(
                f"Unsupported file type: {extension}"
            )

        processed_document = ExtractionService.preprocess_document(raw_text)

        processed_document["file_name"] = Path(file_path).name
        processed_document["file_type"] = extension
        processed_document["file_path"] = str(file_path)

        return processed_document