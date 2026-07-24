import unittest
from services.certification_repository import CertificationRepository


class CertificationRepositoryTests(unittest.TestCase):
    def test_repository_and_aliases(self):
        repo = CertificationRepository()
        self.assertGreater(repo.total_certifications(), 0)
        first = repo.get_all_certifications()[0]
        self.assertTrue(repo.is_valid_certification(first))
        aliases = repo.get_aliases(first)
        if aliases:
            self.assertEqual(repo.normalize_certification(aliases[0]), first)


if __name__ == "__main__":
    unittest.main()
