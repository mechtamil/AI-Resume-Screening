import unittest
from parser.extractors.education_extractor import EducationExtractor


class FakeEducationRepository:
    def get_all_degrees(self): return ["Bachelor of Engineering", "Master of Engineering"]
    def get_aliases(self, degree): return {"Bachelor of Engineering": ["BE"], "Master of Engineering": ["ME"]}.get(degree, [])
    def normalize_degree(self, value):
        mapping = {"bachelor of engineering": "Bachelor of Engineering", "be": "Bachelor of Engineering", "master of engineering": "Master of Engineering", "me": "Master of Engineering"}
        return mapping.get(str(value).casefold())


class EducationExtractorTests(unittest.TestCase):
    def test_short_alias_requires_configured_case(self):
        original = EducationExtractor.repository
        try:
            EducationExtractor.repository = FakeEducationRepository()
            self.assertEqual(EducationExtractor.extract("Education\nBE Mechanical\nExperience"), ["Bachelor of Engineering"])
            self.assertEqual(EducationExtractor.extract("Please contact me for details."), [])
            self.assertEqual(EducationExtractor.extract("Education\nME\nSkills"), ["Master of Engineering"])
        finally:
            EducationExtractor.repository = original


if __name__ == "__main__": unittest.main()
