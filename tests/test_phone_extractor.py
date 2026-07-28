import unittest
from parser.extractors.phone_extractor import PhoneExtractor


class PhoneExtractorTests(unittest.TestCase):
    def test_extract_indian_mobile(self):
        result = PhoneExtractor().extract("Call +91 9876543210")
        self.assertEqual(result["value"], "9876543210")


if __name__ == "__main__":
    unittest.main()
