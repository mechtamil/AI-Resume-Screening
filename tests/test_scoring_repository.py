import unittest
from services.scoring_repository import ScoringRepository


class ScoringRepositoryTests(unittest.TestCase):
    def test_weights_are_numeric_and_total_100(self):
        repo = ScoringRepository()
        self.assertGreater(repo.total_components(), 0)
        self.assertTrue(repo.validate_total_weight(100))
        self.assertTrue(all(weight >= 0 for weight in repo.get_all_weights().values()))


if __name__ == "__main__":
    unittest.main()
