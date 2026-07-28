import sqlite3
import tempfile
import unittest
from pathlib import Path

from database.database import Database


class DatabaseTests(unittest.TestCase):
    def test_create_tables_and_schema_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.db"
            db = Database(path)
            db.create_tables()
            names = {
                row[0]
                for row in db.connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            self.assertTrue(
                {
                    "schema_migrations",
                    "tenants",
                    "users",
                    "tenant_memberships",
                    "auth_sessions",
                    "recruitment_projects",
                    "screening_sessions",
                    "candidates",
                    "resumes",
                    "match_results",
                    "roles",
                    "permissions",
                    "role_permissions",
                    "user_role_assignments",
                    "audit_events",
                    "password_reset_requests",
                    "user_import_jobs",
                    "tenant_configuration_versions",
                }.issubset(names)
            )
            self.assertEqual(db.get_schema_version(), Database.SCHEMA_VERSION)
            self.assertTrue(
                {"tenant_id", "owner_user_id"}.issubset(
                    db.table_columns("recruitment_projects")
                )
            )
            self.assertTrue(
                {"tenant_id", "created_by_user_id"}.issubset(
                    db.table_columns("candidates")
                )
            )
            self.assertTrue(
                {
                    "employee_user_id",
                    "role_code",
                    "account_status",
                    "must_change_password",
                    "temporary_password_expires_at",
                }.issubset(db.table_columns("users"))
            )
            self.assertTrue(
                {
                    "configuration_version_id",
                    "configuration_sha256",
                    "configuration_snapshot_json",
                }.issubset(db.table_columns("screening_sessions"))
            )
            role_codes = {
                row[0]
                for row in db.connection.execute(
                    "SELECT role_code FROM roles WHERE is_active = 1"
                )
            }
            self.assertEqual(
                role_codes,
                {"SYSTEM_OWNER", "GLOBAL_ADMIN", "TENANT_ADMIN", "USER", "READER"},
            )
            db.close()

    def test_schema_three_user_is_upgraded_to_system_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "schema3.db"
            db = Database(path)
            db._create_migration_table()
            db._migration_1_create_core_tables()
            db._record_migration(1)
            db._migration_2_add_persistence_contracts()
            db._record_migration(2)
            db._migration_3_add_multi_user_security()
            db._record_migration(3)
            now = db._utc_now()
            tenant = db.connection.execute(
                """
                INSERT INTO tenants (tenant_key, name, status, created_at, updated_at)
                VALUES ('schema3-tenant', 'Schema 3 User', 'active', ?, ?)
                """,
                (now, now),
            )
            user = db.connection.execute(
                """
                INSERT INTO users
                (user_key, email, email_normalized, display_name, password_hash,
                 password_salt, password_iterations, status, created_at, updated_at)
                VALUES ('schema3-user', 'old@example.com', 'old@example.com',
                        'Existing User', '!', '!', 100000, 'active', ?, ?)
                """,
                (now, now),
            )
            db.connection.execute(
                """
                INSERT INTO tenant_memberships
                (tenant_id, user_id, role, status, created_at)
                VALUES (?, ?, 'owner', 'active', ?)
                """,
                (int(tenant.lastrowid), int(user.lastrowid), now),
            )
            db.connection.commit()
            db.close()

            upgraded = Database(path)
            upgraded.create_tables()
            row = upgraded.connection.execute(
                """
                SELECT employee_user_id, role_code, account_status
                FROM users WHERE user_key = 'schema3-user'
                """
            ).fetchone()
            self.assertEqual(upgraded.get_schema_version(), 5)
            self.assertEqual(row["role_code"], "SYSTEM_OWNER")
            self.assertEqual(row["account_status"], "ACTIVE")
            self.assertTrue(str(row["employee_user_id"]).startswith("U"))
            upgraded.close()

    def test_legacy_database_is_migrated_and_assigned_to_disabled_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.db"
            connection = sqlite3.connect(path)
            connection.executescript(
                """
                CREATE TABLE recruitment_projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT,
                    client_name TEXT,
                    job_title TEXT,
                    hiring_manager TEXT,
                    location TEXT,
                    target_headcount INTEGER,
                    status TEXT
                );
                CREATE TABLE candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    experience REAL,
                    current_company TEXT,
                    location TEXT,
                    notice_period TEXT,
                    current_ctc TEXT,
                    expected_ctc TEXT,
                    status TEXT
                );
                INSERT INTO recruitment_projects (project_name, job_title)
                VALUES ('Legacy Project', 'Legacy Role');
                INSERT INTO candidates (full_name, email, experience)
                VALUES ('Legacy Candidate', 'legacy@example.com', 4.0);
                """
            )
            connection.commit()
            connection.close()

            db = Database(path)
            db.create_tables()
            self.assertEqual(db.get_schema_version(), Database.SCHEMA_VERSION)

            legacy_user = db.connection.execute(
                "SELECT * FROM users WHERE user_key = ?",
                (Database.LEGACY_USER_KEY,),
            ).fetchone()
            self.assertIsNotNone(legacy_user)
            self.assertEqual(legacy_user["status"], "disabled")

            project = db.connection.execute(
                "SELECT tenant_id, owner_user_id FROM recruitment_projects LIMIT 1"
            ).fetchone()
            candidate = db.connection.execute(
                "SELECT tenant_id, created_by_user_id FROM candidates LIMIT 1"
            ).fetchone()
            self.assertIsNotNone(project["tenant_id"])
            self.assertIsNotNone(project["owner_user_id"])
            self.assertIsNotNone(candidate["tenant_id"])
            self.assertIsNotNone(candidate["created_by_user_id"])
            db.close()


if __name__ == "__main__":
    unittest.main()
