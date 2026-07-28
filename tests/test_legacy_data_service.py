import tempfile
import unittest
from pathlib import Path

from database.database import Database
from models.recruitment_project import RecruitmentProject
from services.legacy_data_service import LegacyDataService
from services.persistence_service import PersistenceService
from tests.security_test_utils import build_analysis_result, create_context


class LegacyDataServiceTests(unittest.TestCase):
    def test_explicit_claim_transfers_legacy_records_to_registered_user(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.db"
            database = Database(path)
            database.create_tables()
            legacy_tenant_id = database.connection.execute(
                "SELECT id FROM tenants WHERE tenant_key = ?",
                (Database.LEGACY_TENANT_KEY,),
            ).fetchone()[0]
            legacy_user_id = database.connection.execute(
                "SELECT id FROM users WHERE user_key = ?",
                (Database.LEGACY_USER_KEY,),
            ).fetchone()[0]
            cursor = database.connection.execute(
                """
                INSERT INTO recruitment_projects
                (tenant_id, owner_user_id, project_key, project_name, job_title,
                 created_at, updated_at)
                VALUES (?, ?, 'job:LEGACY', 'Legacy Project', 'Legacy Role', '', '')
                """,
                (legacy_tenant_id, legacy_user_id),
            )
            legacy_project_id = int(cursor.lastrowid)
            database.connection.commit()
            database.close()

            context = create_context(path, "claim.owner@example.com", "Claim Owner")
            self.assertEqual(PersistenceService.list_projects(context, path), [])

            counts = LegacyDataService.claim_for_user(
                context.login_id,
                path,
            )
            self.assertEqual(counts["projects"], 1)
            projects = PersistenceService.list_projects(context, path)
            self.assertEqual(len(projects), 1)
            self.assertEqual(projects[0]["id"], legacy_project_id)
            self.assertEqual(projects[0]["project_name"], "Legacy Project")


if __name__ == "__main__":
    unittest.main()
