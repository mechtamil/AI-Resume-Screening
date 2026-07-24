import unittest
from parser.extractors.certification_extractor import CertificationExtractor


class FakeCertificationRepository:
    def get_all_certifications(self): return ["CATIA V5", "Project Management Professional"]
    def get_aliases(self, value): return {"CATIA V5": ["CATIA"], "Project Management Professional": ["PMP"]}.get(value, [])
    def normalize_certification(self, value): return value


class CertificationExtractorTests(unittest.TestCase):
    def test_certifications_are_context_aware(self):
        original = CertificationExtractor.repository
        try:
            CertificationExtractor.repository = FakeCertificationRepository()
            self.assertEqual(CertificationExtractor.extract("Skills\nCATIA\nPython"), [])
            self.assertEqual(CertificationExtractor.extract("Certifications\nCATIA\nEducation"), ["CATIA V5"])
            self.assertEqual(CertificationExtractor.extract("PMP certified professional"), ["Project Management Professional"])
        finally:
            CertificationExtractor.repository = original


if __name__ == "__main__": unittest.main()
