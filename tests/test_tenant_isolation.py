import tempfile
import unittest
from pathlib import Path

from services.persistence_service import PersistenceService
from tests.security_test_utils import build_analysis_result, create_context


class TenantIsolationTests(unittest.TestCase):
    def test_user_cannot_list_open_read_or_delete_another_users_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "isolation.db"
            user_a = create_context(path, "user.a@example.com", "User A")
            user_b = create_context(path, "user.b@example.com", "User B")

            saved = PersistenceService.save_analysis_result(
                user_a,
                build_analysis_result(),
                path,
            )

            self.assertEqual(len(PersistenceService.list_projects(user_a, path)), 1)
            self.assertEqual(PersistenceService.list_projects(user_b, path), [])
            self.assertEqual(
                PersistenceService.list_sessions(user_b, saved["project_id"], path),
                [],
            )
            self.assertEqual(
                PersistenceService.list_candidate_records(
                    user_b,
                    project_id=saved["project_id"],
                    session_id=saved["session_id"],
                    database_path=path,
                ),
                [],
            )

            with self.assertRaisesRegex(LookupError, "not available"):
                PersistenceService.load_session(
                    user_b,
                    saved["session_id"],
                    path,
                )

            self.assertFalse(
                PersistenceService.delete_project(
                    user_b,
                    saved["project_id"],
                    path,
                )
            )
            self.assertEqual(len(PersistenceService.list_projects(user_a, path)), 1)

    def test_two_users_can_use_same_job_id_without_colliding(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "isolation.db"
            user_a = create_context(path, "first.user@example.com", "First User")
            user_b = create_context(path, "second.user@example.com", "Second User")

            first = PersistenceService.save_analysis_result(
                user_a,
                build_analysis_result(),
                path,
            )
            second = PersistenceService.save_analysis_result(
                user_b,
                build_analysis_result(),
                path,
            )

            self.assertNotEqual(first["project_id"], second["project_id"])
            self.assertEqual(first["project_key"], "job:JD-100")
            self.assertEqual(second["project_key"], "job:JD-100")
            self.assertEqual(len(PersistenceService.list_projects(user_a, path)), 1)
            self.assertEqual(len(PersistenceService.list_projects(user_b, path)), 1)


if __name__ == "__main__":
    unittest.main()
