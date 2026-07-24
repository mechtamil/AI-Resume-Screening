import tempfile
import unittest
from pathlib import Path
from database.candidate_repository import CandidateRepository


class CandidateRepositoryTests(unittest.TestCase):
    def test_add_and_count_candidate_without_touching_project_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = CandidateRepository(Path(tmp) / "test.db")
            candidate_id = repo.add_candidate("Test Candidate", email="test@example.com")
            self.assertGreater(candidate_id, 0)
            self.assertEqual(repo.get_candidate_count(), 1)
            self.assertEqual(repo.get_all_candidates()[0][1], "Test Candidate")
            repo.close()


if __name__ == "__main__":
    unittest.main()
