import unittest
from models.match_result import MatchResult


class MatchResultTests(unittest.TestCase):
    def test_shortlist_is_explicit_not_hardcoded_score(self):
        result = MatchResult(overall_match_percentage=99, shortlisted=False)
        self.assertFalse(result.is_shortlisted())
        result.shortlisted = True
        self.assertTrue(result.is_shortlisted())
        result.add_remark("Test")
        self.assertEqual(result.remarks, ["Test"])


if __name__ == "__main__": unittest.main()
