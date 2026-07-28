import tempfile
import unittest
from pathlib import Path
from models.resume import Resume


class ResumeModelTests(unittest.TestCase):
    def test_statistics_hash_and_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "resume.txt"
            path.write_text("one two three", encoding="utf-8")
            resume = Resume(file_name=path.name, file_path=str(path), extracted_text="one two three")
            resume.calculate_statistics(); resume.generate_hash(); resume.mark_processed()
            self.assertEqual(resume.word_count, 3)
            self.assertTrue(resume.file_hash)
            self.assertEqual(resume.status, "Processed")


if __name__ == "__main__": unittest.main()
