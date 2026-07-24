import unittest
from parser.resume_parser import ResumeParser
from parser.extractors.skill_extractor import SkillExtractor
from parser.extractors.education_extractor import EducationExtractor
from parser.extractors.certification_extractor import CertificationExtractor


class EmptySkillRepo:
    def get_all_skills(self): return []
    def get_skill_synonyms(self, skill): return []
    def find_standard_skill(self, value): return None
    def total_skills(self): return 0


class EmptyEducationRepo:
    def get_all_degrees(self): return []
    def get_aliases(self, value): return []
    def normalize_degree(self, value): return None


class EmptyCertificationRepo:
    def get_all_certifications(self): return []
    def get_aliases(self, value): return []
    def normalize_certification(self, value): return None


class ResumeParserTests(unittest.TestCase):
    def test_personal_contract_and_explicit_experience(self):
        old = (SkillExtractor.repository, EducationExtractor.repository, CertificationExtractor.repository)
        try:
            SkillExtractor.repository = EmptySkillRepo(); EducationExtractor.repository = EmptyEducationRepo(); CertificationExtractor.repository = EmptyCertificationRepo()
            candidate = ResumeParser.parse({"file_name": "resume.txt", "text": "Tamilvanan A\nEmail: test@example.com\n9+ years of progressive experience"})
            self.assertEqual(candidate.full_name, "Tamilvanan A")
            self.assertEqual(candidate.email, "test@example.com")
            self.assertEqual(candidate.total_experience, 9.0)
        finally:
            SkillExtractor.repository, EducationExtractor.repository, CertificationExtractor.repository = old


if __name__ == "__main__": unittest.main()
