import unittest
from parser.extractors.skill_extractor import SkillExtractor


class FakeSkillRepository:
    def get_all_skills(self): return ["Python", "C++"]
    def get_skill_synonyms(self, skill): return {"Python": ["Py3"], "C++": ["CPP"]}.get(skill, [])
    def find_standard_skill(self, value):
        mapping = {"python": "Python", "py3": "Python", "c++": "C++", "cpp": "C++"}
        return mapping.get(str(value).casefold())
    def total_skills(self): return 2


class SkillExtractorTests(unittest.TestCase):
    def test_alias_and_punctuation_skill_matching(self):
        original = SkillExtractor.repository
        try:
            SkillExtractor.repository = FakeSkillRepository()
            self.assertEqual(SkillExtractor.extract("Experienced in Py3 and C++."), ["Python", "C++"])
            self.assertFalse(SkillExtractor.contains_skill("NoSQL", "Python"))
        finally:
            SkillExtractor.repository = original


if __name__ == "__main__": unittest.main()
