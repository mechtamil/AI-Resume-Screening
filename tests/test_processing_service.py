import tempfile
import unittest
from pathlib import Path
from services.processing_service import ProcessingService


class ProcessingServiceTests(unittest.TestCase):
    def test_end_to_end_text_pipeline_and_failure_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            jd = root / "jd.txt"
            jd.write_text(
                "Engineer\nExperience: 2 to 4 years\nMandatory Skills\nPython\nPreferred Skills\nSQL\nEducation\nBE\nKeywords\nautomotive",
                encoding="utf-8",
            )
            resume = root / "resume.txt"
            resume.write_text(
                "Test Candidate\nEmail: test@example.com\n3 years of experience\nEducation\nBE\nSkills\nPython\nAutomotive projects",
                encoding="utf-8",
            )
            missing = root / "missing.pdf"
            result = ProcessingService.process_documents(jd, [resume, missing], job_id="JD-1")
            self.assertEqual(result["summary"]["resumes_processed"], 1)
            self.assertEqual(result["summary"]["resumes_failed"], 1)
            self.assertEqual(len(result["match_results"]), 1)
            self.assertEqual(result["match_results"][0].rank, 1)
            self.assertEqual(result["match_results"][0].candidate_name, "Test Candidate")


if __name__ == "__main__": unittest.main()
