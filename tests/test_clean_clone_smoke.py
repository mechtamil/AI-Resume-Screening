import unittest
from pathlib import Path


class CleanCloneSmokeTests(unittest.TestCase):
    def test_required_runtime_files_are_present(self):
        root = Path(__file__).resolve().parent.parent
        self.assertTrue((root / "parser" / "extractors" / "skill_extractor.py").is_file())
        self.assertFalse((root / "parser" / "extractors" / "skills_extractor.py").exists())
        self.assertTrue((root / "Master_Data" / "RecruitOS_Configuration.xlsx").is_file())

    def test_core_imports(self):
        from parser.resume_parser import ResumeParser
        from JD.jd_parser import JDParser
        from services.matching.matching_orchestrator import MatchingOrchestrator
        self.assertIsNotNone(ResumeParser)
        self.assertIsNotNone(JDParser)
        self.assertIsNotNone(MatchingOrchestrator)


if __name__ == "__main__": unittest.main()
