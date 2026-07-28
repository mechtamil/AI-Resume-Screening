import tempfile
import unittest
from pathlib import Path

import fitz
from docx import Document

from services.document_manager import DocumentManager


class DocumentManagerTests(unittest.TestCase):
    def test_txt_docx_pdf_contract_and_missing_file_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            txt = root / "sample.txt"
            txt.write_text("Hello RecruitOS", encoding="utf-8")

            docx = root / "sample.docx"
            document = Document()
            document.add_paragraph("Hello DOCX")
            document.save(docx)

            pdf = root / "sample.pdf"
            pdf_doc = fitz.open()
            page = pdf_doc.new_page()
            page.insert_text((72, 72), "Hello PDF")
            pdf_doc.save(pdf)
            pdf_doc.close()

            for path, expected in ((txt, "Hello RecruitOS"), (docx, "Hello DOCX"), (pdf, "Hello PDF")):
                result = DocumentManager.read_document(path)
                self.assertIsInstance(result, dict)
                self.assertIn(expected, result["text"])
                self.assertEqual(result["file_name"], path.name)

            with self.assertRaises(FileNotFoundError):
                DocumentManager.read_document(root / "missing.pdf")


if __name__ == "__main__":
    unittest.main()
