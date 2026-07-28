import unittest
from JD.jd_model import JobDescription
from models.candidate import Candidate
from models.match_result import MatchResult
from services.matching.experience_matcher import ExperienceMatcher


class ExperienceMatcherTests(unittest.TestCase):
    def test_partial_and_full_score(self):
        job = JobDescription(experience_min=4, experience_max=8)
        low = ExperienceMatcher.match(Candidate(total_experience=2), job, MatchResult())
        self.assertFalse(low.experience_match)
        self.assertEqual(low.experience_score, 50.0)
        high = ExperienceMatcher.match(Candidate(total_experience=6), job, MatchResult())
        self.assertTrue(high.experience_match)
        self.assertEqual(high.experience_score, 100.0)


if __name__ == "__main__": unittest.main()
