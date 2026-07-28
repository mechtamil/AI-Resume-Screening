import unittest
from JD.jd_model import JobDescription
from models.candidate import Candidate
from services.matching.matching_orchestrator import MatchingOrchestrator


class ResultsDataTests(unittest.TestCase):
    def test_result_contract_contains_ranked_match(self):
        job = JobDescription(job_title="Technical Writer", mandatory_skills=["Python"])
        candidate = Candidate(full_name="Test Candidate", technical_skills=["Python"], raw_text="Python")
        matches = MatchingOrchestrator().match_many(job, [candidate])
        result = {"job_description": job, "candidates": [candidate], "match_results": matches}
        self.assertEqual(result["match_results"][0].rank, 1)
        self.assertEqual(result["match_results"][0].candidate_name, "Test Candidate")


if __name__ == "__main__": unittest.main()
