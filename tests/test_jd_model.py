import unittest
from JD.jd_model import JobDescription
from models.job_description import JobDescription as CompatibilityJobDescription


class JobDescriptionModelTests(unittest.TestCase):
    def test_single_authoritative_model(self):
        self.assertIs(JobDescription, CompatibilityJobDescription)
        job = JobDescription(job_title="Engineer", mandatory_skills=["Python"])
        self.assertEqual(job.total_required_skills(), 1)
        self.assertEqual(job.summary()["Job Title"], "Engineer")


if __name__ == "__main__":
    unittest.main()
