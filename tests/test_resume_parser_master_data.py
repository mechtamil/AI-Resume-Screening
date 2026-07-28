import unittest
from parser.resume_parser import ResumeParser
from parser.extractors.skill_extractor import SkillExtractor
from parser.extractors.education_extractor import EducationExtractor
from parser.extractors.certification_extractor import CertificationExtractor


class SkillRepo:
    def get_all_skills(self): return ["Python"]
    def get_skill_synonyms(self, skill): return ["Py3"]
    def find_standard_skill(self, value): return "Python" if str(value).casefold() in {"python", "py3"} else None
    def total_skills(self): return 1


class EduRepo:
    def get_all_degrees(self): return ["Configured Degree"]
    def get_aliases(self, value): return ["CD"]
    def normalize_degree(self, value): return "Configured Degree" if str(value).casefold() in {"configured degree", "cd"} else None


class CertRepo:
    def get_all_certifications(self): return ["Configured Certification"]
    def get_aliases(self, value): return ["CC"]
    def normalize_certification(self, value): return "Configured Certification" if str(value).casefold() in {"configured certification", "cc"} else None


class ResumeMasterDataTests(unittest.TestCase):
    def test_resume_parser_populates_configured_master_data(self):
        old = (SkillExtractor.repository, EducationExtractor.repository, CertificationExtractor.repository)
        try:
            SkillExtractor.repository = SkillRepo(); EducationExtractor.repository = EduRepo(); CertificationExtractor.repository = CertRepo()
            text = "Test Candidate\n6 years of experience\nEducation\nCD\nCertifications\nCC\nSkills\nPy3"
            candidate = ResumeParser.parse({"file_name": "test.txt", "text": text})
            self.assertEqual(candidate.full_name, "Test Candidate")
            self.assertEqual(candidate.education, ["Configured Degree"])
            self.assertEqual(candidate.certifications, ["Configured Certification"])
            self.assertEqual(candidate.technical_skills, ["Python"])
            self.assertEqual(candidate.total_experience, 6.0)
        finally:
            SkillExtractor.repository, EducationExtractor.repository, CertificationExtractor.repository = old


if __name__ == "__main__": unittest.main()
