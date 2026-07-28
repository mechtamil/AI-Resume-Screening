import tempfile
import unittest
from pathlib import Path

from models.storage_asset import StorageScope
from services.persistence_service import PersistenceService
from services.secure_storage_service import SecureStorageService
from tests.security_test_utils import build_analysis_result, create_context


class PersistenceServiceTests(unittest.TestCase):
    def test_save_and_reopen_complete_private_screening_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.db"
            context = create_context(path, "persistence@example.com")
            result = build_analysis_result()
            result["storage"] = {"workspace_id": "a" * 32}
            saved = PersistenceService.save_analysis_result(context, result, path)
            self.assertGreater(saved["project_id"], 0)
            self.assertGreater(saved["session_id"], 0)
            self.assertEqual(saved["tenant_id"], context.tenant_id)
            self.assertEqual(saved["owner_user_id"], context.user_id)
            self.assertEqual(saved["candidates_saved"], 1)
            self.assertEqual(saved["matches_saved"], 1)
            self.assertEqual(saved["session_key"], "a" * 32)

            reopened = PersistenceService.load_session(
                context,
                saved["session_id"],
                path,
            )
            self.assertEqual(reopened["project"]["project_name"], "Volvo Hiring")
            self.assertEqual(
                reopened["job_description"].job_title,
                "Documentation Engineer",
            )
            self.assertEqual(reopened["candidates"][0].full_name, "Candidate One")
            self.assertEqual(
                reopened["match_results"][0].recommendation,
                "Highly Recommended",
            )
            self.assertTrue(reopened["match_results"][0].shortlisted)
            self.assertEqual(reopened["storage"]["workspace_id"], "a" * 32)

    def test_same_job_creates_new_session_under_existing_private_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.db"
            context = create_context(path, "repeat@example.com")
            first = PersistenceService.save_analysis_result(
                context,
                build_analysis_result(),
                path,
            )
            second = PersistenceService.save_analysis_result(
                context,
                build_analysis_result(),
                path,
            )
            self.assertEqual(first["project_id"], second["project_id"])
            self.assertNotEqual(first["session_id"], second["session_id"])
            self.assertEqual(len(PersistenceService.list_projects(context, path)), 1)
            self.assertEqual(
                len(
                    PersistenceService.list_sessions(
                        context,
                        first["project_id"],
                        path,
                    )
                ),
                2,
            )

    def test_delete_project_removes_only_owner_file_workspaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database_path = root / "test.db"
            storage = SecureStorageService(
                uploads_root=root / "uploads",
                temp_root=root / "temp",
                output_root=root / "output",
            )
            owner = create_context(database_path, "delete-owner@example.com")
            other = create_context(database_path, "delete-other@example.com")
            owner_scope = storage.create_scope(owner, "b" * 32)
            other_scope = storage.create_scope(other, "c" * 32)
            owner_file = storage.save_temp_bytes(owner, owner_scope, "owner.txt", b"owner")
            other_file = storage.save_temp_bytes(other, other_scope, "other.txt", b"other")

            result = build_analysis_result()
            result["storage"] = owner_scope.summary()
            saved = PersistenceService.save_analysis_result(owner, result, database_path)

            self.assertTrue(
                PersistenceService.delete_project(
                    owner,
                    saved["project_id"],
                    database_path,
                    storage,
                )
            )
            self.assertFalse(owner_file.absolute_path.exists())
            self.assertTrue(other_file.absolute_path.exists())



if __name__ == "__main__":
    unittest.main()
