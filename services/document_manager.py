"""
============================================================
RecruitOS
Document Manager
Version : 0.6
Author  : Tamilvanan A

Description:
Reads any supported document by automatically selecting
the correct reader.

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


class DocumentManager:

    @staticmethod
    def read_document(file_path: str) -> str:

        extension = Path(file_path).suffix.lower()

        if extension == ".pdf":
            return read_pdf(file_path)

        elif extension == ".docx":
            return read_docx(file_path)

        elif extension == ".txt":
            return read_txt(file_path)

        raise ValueError(
            f"Unsupported file type: {extension}"
        )