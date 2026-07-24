import unittest
from services.recommendation_repository import RecommendationRepository


class RecommendationRepositoryTests(unittest.TestCase):
    def test_continuous_decimal_coverage(self):
        repo = RecommendationRepository()
        self.assertTrue(repo.validate_coverage(0, 100))
        for score in (0, 59.5, 60, 74.5, 75, 89.5, 90, 100):
            self.assertIsNotNone(repo.get_recommendation(score), score)
        self.assertEqual(repo.require_recommendation(100), repo.get_recommendation(100))


if __name__ == "__main__":
    unittest.main()
