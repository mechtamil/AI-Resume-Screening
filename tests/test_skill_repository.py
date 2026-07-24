import unittest
from services.skill_repository import SkillRepository


class SkillRepositoryTests(unittest.TestCase):
    def test_repository_and_alias_normalization(self):
        repo = SkillRepository()
        self.assertGreater(repo.total_skills(), 0)
        first = repo.get_all_skills()[0]
        self.assertTrue(repo.is_valid_skill(first))
        self.assertEqual(repo.normalize_skill(first), first)
        aliases = repo.get_skill_synonyms(first)
        if aliases:
            self.assertEqual(repo.normalize_skill(aliases[0]), first)


if __name__ == "__main__":
    unittest.main()
