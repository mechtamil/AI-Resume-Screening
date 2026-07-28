"""Tests for common-format document normalization and OCR adapters."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from PIL import Image

from JD.jd_parser import JDParser
from services.document_manager import DocumentManager


class DocumentManagerMultiFormatTests(unittest.TestCase):
    def test_xlsx_job_description_is_normalized_for_jd_parser(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "jd.xlsx"
            frame = pd.DataFrame(
                [
                    ["Job Title", "Documentation Engineer"],
                    ["Company Name", "ALTEN"],
                    ["Experience", "3 to 5 years"],
                    ["Mandatory Skills", "Python\nSQL"],
                    ["Preferred Skills", "Docker"],
                    ["Education", "Bachelor of Engineering"],
                ],
                columns=["Field", "Value"],
            )
            frame.to_excel(path, index=False)

            document = DocumentManager.read_document(path)
            job = JDParser.parse(document)

            self.assertEqual(job.job_title, "Documentation Engineer")
            self.assertEqual(job.company_name, "ALTEN")
            self.assertEqual(job.experience_min, 3.0)
            self.assertEqual(job.experience_max, 5.0)
            self.assertIn("Python", job.mandatory_skills)
            self.assertIn("SQL", job.mandatory_skills)
            self.assertIn("Docker", job.preferred_skills)

    def test_csv_resume_is_converted_to_readable_text(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "resume.csv"
            pd.DataFrame(
                [{"Name": "Test Candidate", "Email": "test@example.com", "Skills": "Python"}]
            ).to_csv(path, index=False)

            document = DocumentManager.read_document(path)

            self.assertIn("Name: Test Candidate", document["text"])
            self.assertIn("Email: test@example.com", document["text"])
            self.assertEqual(document["file_type"], ".csv")

    def test_image_uses_ocr_reader(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "resume.png"
            Image.new("RGB", (20, 20), "white").save(path)

            with patch("parser.image_reader._ocr_image", return_value="Image Candidate\nPython"):
                document = DocumentManager.read_document(path)

            self.assertIn("Image Candidate", document["text"])
            self.assertEqual(document["file_type"], ".png")

    def test_empty_extraction_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.txt"
            path.write_text("   ", encoding="utf-8")
            with self.assertRaises(ValueError):
                DocumentManager.read_document(path)


if __name__ == "__main__":
    unittest.main()
