import unittest
from JD.jd_model import JobDescription
from models.candidate import Candidate
from models.match_result import MatchResult
from services.matching.education_matcher import EducationMatcher


class EducationMatcherTests(unittest.TestCase):
    def test_match_and_no_requirement(self):
        job = JobDescription(education=["Bachelor of Engineering"])
        result = EducationMatcher.match(Candidate(education=["Bachelor of Engineering"]), job, MatchResult())
        self.assertTrue(result.education_match)
        self.assertEqual(result.education_score, 100.0)
        neutral = EducationMatcher.match(Candidate(), JobDescription(), MatchResult())
        self.assertEqual(neutral.education_score, 100.0)


if __name__ == "__main__": unittest.main()
