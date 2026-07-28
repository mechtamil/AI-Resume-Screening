import unittest
from models.match_result import MatchResult
from services.matching.score_calculator import ScoreCalculator


class ScoreCalculatorTests(unittest.TestCase):
    def test_configuration_driven_weighted_score(self):
        result = MatchResult(skill_score=100, experience_score=100, education_score=100, certification_score=100, keyword_score=100)
        ScoreCalculator().calculate(result)
        self.assertEqual(result.overall_match_percentage, 100.0)
        self.assertAlmostEqual(sum(result.weighted_score_breakdown.values()), 100.0)


if __name__ == "__main__": unittest.main()
