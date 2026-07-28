import tempfile
import unittest
from pathlib import Path

from database.candidate_repository import CandidateRepository
from models.candidate import Candidate
from tests.security_test_utils import create_context


class CandidateRepositoryTests(unittest.TestCase):
    def test_domain_candidate_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.db"
            context = create_context(path, "candidate.owner@example.com")
            repo = CandidateRepository(context, path)
            candidate = Candidate(
                full_name="Test Candidate",
                email="test@example.com",
                phone="9999999999",
                location="Chennai",
                total_experience=6.5,
                education=["Bachelor of Engineering"],
                certifications=["Test Certification"],
                technical_skills=["Python", "SQL"],
                source_file="test_resume.pdf",
                raw_text="Resume text",
            )
            candidate_id = repo.add_candidate_model(candidate)
            restored = repo.get_candidate(candidate_id)
            self.assertIsNotNone(restored)
            self.assertEqual(restored.full_name, "Test Candidate")
            self.assertEqual(restored.total_experience, 6.5)
            self.assertEqual(restored.education, ["Bachelor of Engineering"])
            self.assertEqual(restored.technical_skills, ["Python", "SQL"])
            repo.close()

    def test_backward_compatible_add_and_count_is_user_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.db"
            owner = create_context(path, "owner@example.com", "Owner")
            other = create_context(path, "other@example.com", "Other")

            owner_repo = CandidateRepository(owner, path)
            candidate_id = owner_repo.add_candidate(
                "Test Candidate",
                email="test@example.com",
            )
            self.assertGreater(candidate_id, 0)
            self.assertEqual(owner_repo.get_candidate_count(), 1)
            self.assertEqual(owner_repo.get_all_candidates()[0][1], "Test Candidate")
            owner_repo.close()

            other_repo = CandidateRepository(other, path)
            self.assertEqual(other_repo.get_candidate_count(), 0)
            self.assertEqual(other_repo.get_all_candidates(), [])
            self.assertIsNone(other_repo.get_candidate(candidate_id))
            other_repo.close()


if __name__ == "__main__":
    unittest.main()
