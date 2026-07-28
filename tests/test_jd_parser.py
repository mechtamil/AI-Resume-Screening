import unittest
from JD.jd_parser import JDParser


SAMPLE = """Technical Documentation Engineer
Client:
Volvo
Experience:
4 to 8 Years
Location:
Bangalore
Mandatory Skills
DITA
XML
Arbortext
Technical Publications
Preferred Skills
Python
Automotive Domain
FrameMaker
Education
BE Mechanical
Responsibilities
Create Technical Documentation
Work with Global Teams
"""


class JDParserTests(unittest.TestCase):
    def test_sections_do_not_bleed_into_each_other(self):
        job = JDParser.parse({"file_name": "sample.txt", "text": SAMPLE})
        self.assertEqual(job.job_title, "Technical Documentation Engineer")
        self.assertEqual(job.company_name, "Volvo")
        self.assertEqual(job.location, "Bangalore")
        self.assertEqual((job.experience_min, job.experience_max), (4.0, 8.0))
        self.assertIn("Arbortext Editor", job.mandatory_skills)
        self.assertIn("Python", job.preferred_skills)
        self.assertNotIn("Preferred Skills", job.mandatory_skills)
        self.assertNotIn("Education", job.mandatory_skills)
        self.assertEqual(job.education, ["Bachelor of Engineering"])
        self.assertEqual(job.responsibilities, ["Create Technical Documentation", "Work with Global Teams"])


if __name__ == "__main__":
    unittest.main()
