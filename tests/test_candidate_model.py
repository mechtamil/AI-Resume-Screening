import unittest
from models.candidate import Candidate


class CandidateModelTests(unittest.TestCase):
    def test_summary_and_counts(self):
        candidate = Candidate(full_name="Test Candidate", technical_skills=["Python"], tools=["Git"], certifications=["Cert"])
        self.assertEqual(candidate.total_skills(), 2)
        self.assertEqual(candidate.total_certifications(), 1)
        self.assertEqual(candidate.summary()["Candidate"], "Test Candidate")


if __name__ == "__main__":
    unittest.main()
