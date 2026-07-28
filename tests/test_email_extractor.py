import unittest
from parser.extractors.email_extractor import EmailExtractor


class EmailExtractorTests(unittest.TestCase):
    def test_extract(self):
        result = EmailExtractor().extract("Contact Test.User@example.com")
        self.assertEqual(result["value"], "test.user@example.com")
        self.assertGreater(result["confidence"], 0)


if __name__ == "__main__":
    unittest.main()
