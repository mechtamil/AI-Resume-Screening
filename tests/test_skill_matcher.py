import unittest
from JD.jd_model import JobDescription
from models.candidate import Candidate
from services.matching.skill_matcher import SkillMatcher


class SkillMatcherTests(unittest.TestCase):
    def test_mandatory_preferred_and_canonical_casing(self):
        candidate = Candidate(full_name="Test", technical_skills=["Python", "SQL", "Docker"])
        job = JobDescription(job_title="Engineer", mandatory_skills=["Python", "Java"], preferred_skills=["SQL"])
        result = SkillMatcher.match(candidate, job)
        self.assertEqual(result.matched_skills, ["Python"])
        self.assertEqual(result.missing_skills, ["Java"])
        self.assertEqual(result.matched_preferred_skills, ["SQL"])
        self.assertEqual(result.additional_skills, ["Docker"])
        self.assertEqual(result.skill_score, 50.0)


if __name__ == "__main__": unittest.main()
