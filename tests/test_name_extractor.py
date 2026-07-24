import unittest
from parser.extractors.name_extractor import NameExtractor


class NameExtractorTests(unittest.TestCase):
    def test_allows_single_letter_initial_and_skips_contact_lines(self):
        text = "Ajay Goud G\nEmail: ajay@example.com\nExperience"
        self.assertEqual(NameExtractor().extract(text), "Ajay Goud G")

    def test_skips_personal_details_heading(self):
        text = "Personal Details\nPriyesh S\nEMAIL: p@example.com"
        self.assertEqual(NameExtractor().extract(text), "Priyesh S")


if __name__ == "__main__":
    unittest.main()
