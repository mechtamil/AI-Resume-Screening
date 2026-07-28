import unittest
from services.configuration_validator import ConfigurationValidator


class ConfigurationValidatorTests(unittest.TestCase):
    def test_current_configuration_preflight(self):
        report = ConfigurationValidator.validate_or_raise()
        self.assertTrue(report["valid"])
        self.assertEqual(report["errors"], [])


if __name__ == "__main__": unittest.main()
