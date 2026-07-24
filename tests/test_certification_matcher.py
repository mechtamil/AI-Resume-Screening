import unittest
from JD.jd_model import JobDescription
from models.candidate import Candidate
from models.match_result import MatchResult
from services.matching.certification_matcher import CertificationMatcher


class CertificationMatcherTests(unittest.TestCase):
    def test_declared_match_contract(self):
        result = CertificationMatcher.match(Candidate(certifications=["PMP"]), JobDescription(certifications=["PMP"]), MatchResult())
        self.assertTrue(result.certification_match)
        self.assertEqual(result.certification_score, 100.0)
        self.assertEqual(result.matched_certifications, ["PMP"])


if __name__ == "__main__": unittest.main()
