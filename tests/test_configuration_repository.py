import unittest
from services.configuration_repository import ConfigurationRepository


class ConfigurationRepositoryTests(unittest.TestCase):
    def test_key_value_access(self):
        repo = ConfigurationRepository()
        self.assertEqual(str(repo.get("Product")), "RecruitOS")
        self.assertIsNone(repo.get_float("Shortlist Minimum Score", None))


if __name__ == "__main__": unittest.main()
