import tempfile
import unittest
from pathlib import Path
from services.processing_service import ProcessingService


class EndToEndTests(unittest.TestCase):
    def test_parse_match_score_rank_recommend(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            jd = root / "jd.txt"
            jd.write_text(
                "Job Title: Documentation Engineer\nExperience: 2 to 5 years\nMandatory Skills\nPython\nSQL\nPreferred Skills\nDocker\nEducation\nBE\nKeywords\nautomotive",
                encoding="utf-8",
            )
            resume1 = root / "one.txt"
            resume1.write_text("Candidate One\n3 years of experience\nEducation\nBE\nSkills\nPython SQL Docker\nAutomotive", encoding="utf-8")
            resume2 = root / "two.txt"
            resume2.write_text("Candidate Two\n1 years of experience\nSkills\nPython", encoding="utf-8")
            result = ProcessingService.process_documents(jd, [resume1, resume2])
            self.assertEqual(len(result["match_results"]), 2)
            self.assertEqual([m.rank for m in result["match_results"]], [1, 2])
            self.assertGreaterEqual(result["match_results"][0].overall_match_percentage, result["match_results"][1].overall_match_percentage)
            self.assertTrue(all(m.recommendation for m in result["match_results"]))


if __name__ == "__main__": unittest.main()
