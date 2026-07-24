import unittest
from models.recruitment_project import RecruitmentProject


class RecruitmentProjectTests(unittest.TestCase):
    def test_summary(self):
        project = RecruitmentProject(project_name="Project", target_headcount=5)
        self.assertEqual(project.summary()["Target HC"], 5)


if __name__ == "__main__": unittest.main()
