import unittest
from JD.jd_model import JobDescription
from models.candidate import Candidate
from services.matching_engine import MatchingEngine


class MatchingEngineTests(unittest.TestCase):
    def test_legacy_facade_uses_modular_orchestrator(self):
        job = JobDescription(job_title="Engineer", mandatory_skills=["Python"])
        candidate = Candidate(full_name="Candidate", technical_skills=["Python"], raw_text="Python")
        result = MatchingEngine.match(job, candidate)
        self.assertEqual(result.candidate_name, "Candidate")
        self.assertEqual(result.skill_score, 100.0)
        self.assertTrue(0 <= result.overall_match_percentage <= 100)
        self.assertTrue(result.recommendation)
        self.assertIsInstance(result.remarks, list)


if __name__ == "__main__": unittest.main()
