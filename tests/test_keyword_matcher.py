import unittest
from JD.jd_model import JobDescription
from models.candidate import Candidate
from models.match_result import MatchResult
from services.matching.keyword_matcher import KeywordMatcher


class KeywordMatcherTests(unittest.TestCase):
    def test_keyword_percentage(self):
        job = JobDescription(keywords=["automotive", "diagnostics"])
        candidate = Candidate(raw_text="Automotive documentation experience")
        result = KeywordMatcher.match(candidate, job, MatchResult())
        self.assertEqual(result.keyword_score, 50.0)
        self.assertEqual(result.matched_keyword_values, ["automotive"])


if __name__ == "__main__": unittest.main()
