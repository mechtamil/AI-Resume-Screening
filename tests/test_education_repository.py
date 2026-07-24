import unittest
from services.education_repository import EducationRepository


class EducationRepositoryTests(unittest.TestCase):
    def test_repository_and_aliases(self):
        repo = EducationRepository()
        self.assertGreaterEqual(repo.total_degrees(), 1)
        first = repo.get_all_degrees()[0]
        self.assertTrue(repo.is_valid_degree(first))
        aliases = repo.get_aliases(first)
        if aliases:
            self.assertEqual(repo.normalize_degree(aliases[0]), first)


if __name__ == "__main__":
    unittest.main()
