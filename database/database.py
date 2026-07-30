"""SQLite connection, schema migrations, and transaction support for RecruitOS."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from config.paths import DATABASE_PATH


class Database:
    """Own a SQLite connection and apply idempotent schema migrations."""

    SCHEMA_VERSION = 7
    LEGACY_TENANT_KEY = "legacy-imported-data"
    LEGACY_USER_KEY = "legacy-imported-user"
    LEGACY_USER_EMAIL = "legacy-imported@recruitos.local"

    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = Path(database_path or DATABASE_PATH)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA busy_timeout = 5000")
        self.cursor = self.connection.cursor()

    def create_tables(self) -> None:
        """Create or migrate the database to the current schema version."""
        self._create_migration_table()
        current_version = self.get_schema_version()

        if current_version < 1:
            self._migration_1_create_core_tables()
            self._record_migration(1)

        if current_version < 2:
            self._migration_2_add_persistence_contracts()
            self._record_migration(2)

        if current_version < 3:
            self._migration_3_add_multi_user_security()
            self._record_migration(3)

        if current_version < 4:
            self._migration_4_add_admin_provisioning_rbac()
            self._record_migration(4)

        if current_version < 5:
            self._migration_5_add_tenant_configuration_versions()
            self._record_migration(5)

        if current_version < 6:
            self._migration_6_add_explicit_record_sharing()
            self._record_migration(6)

        if current_version < 7:
            self._migration_7_add_ai_provider_gateway()
            self._record_migration(7)

        self.connection.commit()

    def get_schema_version(self) -> int:
        self._create_migration_table()
        row = self.connection.execute(
            "SELECT COALESCE(MAX(version), 0) AS version FROM schema_migrations"
        ).fetchone()
        return int(row["version"] if row else 0)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Run a multi-repository operation atomically."""
        try:
            self.connection.execute("BEGIN")
            yield self.connection
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def table_columns(self, table_name: str) -> set[str]:
        rows = self.connection.execute(
            f'PRAGMA table_info("{table_name}")'
        ).fetchall()
        return {str(row["name"]) for row in rows}

    def table_exists(self, table_name: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (str(table_name),),
        ).fetchone()
        return row is not None

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def _create_migration_table(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def _record_migration(self, version: int) -> None:
        self.connection.execute(
            """
            INSERT OR IGNORE INTO schema_migrations (version, applied_at)
            VALUES (?, ?)
            """,
            (version, self._utc_now()),
        )

    def _migration_1_create_core_tables(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS recruitment_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_key TEXT,
                project_name TEXT NOT NULL DEFAULT '',
                client_name TEXT NOT NULL DEFAULT '',
                job_id TEXT NOT NULL DEFAULT '',
                job_title TEXT NOT NULL DEFAULT '',
                hiring_manager TEXT NOT NULL DEFAULT '',
                location TEXT NOT NULL DEFAULT '',
                target_headcount INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'Open',
                jd_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS screening_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                session_key TEXT NOT NULL,
                resumes_requested INTEGER NOT NULL DEFAULT 0,
                resumes_processed INTEGER NOT NULL DEFAULT 0,
                resumes_failed INTEGER NOT NULL DEFAULT 0,
                shortlisted_count INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'Completed',
                errors_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id)
                    REFERENCES recruitment_projects(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                session_id INTEGER,
                candidate_key TEXT NOT NULL DEFAULT '',
                full_name TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                location TEXT NOT NULL DEFAULT '',
                linkedin TEXT NOT NULL DEFAULT '',
                github TEXT NOT NULL DEFAULT '',
                website TEXT NOT NULL DEFAULT '',
                designation TEXT NOT NULL DEFAULT '',
                experience REAL NOT NULL DEFAULT 0,
                total_experience REAL NOT NULL DEFAULT 0,
                current_company TEXT NOT NULL DEFAULT '',
                notice_period TEXT NOT NULL DEFAULT '',
                current_ctc TEXT NOT NULL DEFAULT '',
                expected_ctc TEXT NOT NULL DEFAULT '',
                education_json TEXT NOT NULL DEFAULT '[]',
                certifications_json TEXT NOT NULL DEFAULT '[]',
                technical_skills_json TEXT NOT NULL DEFAULT '[]',
                soft_skills_json TEXT NOT NULL DEFAULT '[]',
                tools_json TEXT NOT NULL DEFAULT '[]',
                projects_json TEXT NOT NULL DEFAULT '[]',
                companies_json TEXT NOT NULL DEFAULT '[]',
                source_file TEXT NOT NULL DEFAULT '',
                raw_text TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'New',
                created_at TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (project_id)
                    REFERENCES recruitment_projects(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (session_id)
                    REFERENCES screening_sessions(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                file_name TEXT,
                file_type TEXT,
                file_size INTEGER,
                page_count INTEGER,
                word_count INTEGER,
                character_count INTEGER,
                file_hash TEXT,
                uploaded_time TEXT,
                FOREIGN KEY (candidate_id)
                    REFERENCES candidates(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS match_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                session_id INTEGER NOT NULL,
                candidate_id INTEGER NOT NULL,
                job_id TEXT NOT NULL DEFAULT '',
                job_title TEXT NOT NULL DEFAULT '',
                matched_skills_json TEXT NOT NULL DEFAULT '[]',
                missing_skills_json TEXT NOT NULL DEFAULT '[]',
                matched_preferred_skills_json TEXT NOT NULL DEFAULT '[]',
                missing_preferred_skills_json TEXT NOT NULL DEFAULT '[]',
                additional_skills_json TEXT NOT NULL DEFAULT '[]',
                matched_certifications_json TEXT NOT NULL DEFAULT '[]',
                missing_certifications_json TEXT NOT NULL DEFAULT '[]',
                certification_match INTEGER NOT NULL DEFAULT 0,
                education_match INTEGER NOT NULL DEFAULT 0,
                required_experience REAL NOT NULL DEFAULT 0,
                maximum_experience REAL NOT NULL DEFAULT 0,
                candidate_experience REAL NOT NULL DEFAULT 0,
                experience_match INTEGER NOT NULL DEFAULT 0,
                matched_keyword_values_json TEXT NOT NULL DEFAULT '[]',
                missing_keyword_values_json TEXT NOT NULL DEFAULT '[]',
                matched_keywords INTEGER NOT NULL DEFAULT 0,
                total_keywords INTEGER NOT NULL DEFAULT 0,
                skill_score REAL NOT NULL DEFAULT 0,
                experience_score REAL NOT NULL DEFAULT 0,
                education_score REAL NOT NULL DEFAULT 0,
                certification_score REAL NOT NULL DEFAULT 0,
                keyword_score REAL NOT NULL DEFAULT 0,
                weighted_score_breakdown_json TEXT NOT NULL DEFAULT '{}',
                overall_match_percentage REAL NOT NULL DEFAULT 0,
                rank INTEGER NOT NULL DEFAULT 0,
                recommendation TEXT NOT NULL DEFAULT '',
                shortlisted INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'Pending',
                remarks_json TEXT NOT NULL DEFAULT '[]',
                processed_time TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (project_id)
                    REFERENCES recruitment_projects(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (session_id)
                    REFERENCES screening_sessions(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (candidate_id)
                    REFERENCES candidates(id)
                    ON DELETE CASCADE,
                UNIQUE (session_id, candidate_id)
            );
            """
        )

    def _migration_2_add_persistence_contracts(self) -> None:
        """Upgrade databases created by the original RecruitOS schema."""
        self._migration_1_create_core_tables()

        project_columns = {
            "project_key": "TEXT",
            "job_id": "TEXT NOT NULL DEFAULT ''",
            "jd_json": "TEXT NOT NULL DEFAULT '{}'",
            "created_at": "TEXT NOT NULL DEFAULT ''",
            "updated_at": "TEXT NOT NULL DEFAULT ''",
        }
        candidate_columns = {
            "project_id": "INTEGER",
            "session_id": "INTEGER",
            "candidate_key": "TEXT NOT NULL DEFAULT ''",
            "linkedin": "TEXT NOT NULL DEFAULT ''",
            "github": "TEXT NOT NULL DEFAULT ''",
            "website": "TEXT NOT NULL DEFAULT ''",
            "designation": "TEXT NOT NULL DEFAULT ''",
            "total_experience": "REAL NOT NULL DEFAULT 0",
            "education_json": "TEXT NOT NULL DEFAULT '[]'",
            "certifications_json": "TEXT NOT NULL DEFAULT '[]'",
            "technical_skills_json": "TEXT NOT NULL DEFAULT '[]'",
            "soft_skills_json": "TEXT NOT NULL DEFAULT '[]'",
            "tools_json": "TEXT NOT NULL DEFAULT '[]'",
            "projects_json": "TEXT NOT NULL DEFAULT '[]'",
            "companies_json": "TEXT NOT NULL DEFAULT '[]'",
            "source_file": "TEXT NOT NULL DEFAULT ''",
            "raw_text": "TEXT NOT NULL DEFAULT ''",
            "created_at": "TEXT NOT NULL DEFAULT ''",
        }

        for column, definition in project_columns.items():
            self._ensure_column("recruitment_projects", column, definition)

        for column, definition in candidate_columns.items():
            self._ensure_column("candidates", column, definition)

        self.connection.executescript(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_recruitment_projects_project_key
                ON recruitment_projects(project_key)
                WHERE project_key IS NOT NULL AND project_key <> '';

            CREATE UNIQUE INDEX IF NOT EXISTS ux_screening_sessions_session_key
                ON screening_sessions(session_key);

            CREATE INDEX IF NOT EXISTS ix_screening_sessions_project_id
                ON screening_sessions(project_id, created_at DESC);

            CREATE INDEX IF NOT EXISTS ix_candidates_project_id
                ON candidates(project_id);

            CREATE INDEX IF NOT EXISTS ix_candidates_session_id
                ON candidates(session_id);

            CREATE INDEX IF NOT EXISTS ix_candidates_email
                ON candidates(email);

            CREATE INDEX IF NOT EXISTS ix_match_results_session_rank
                ON match_results(session_id, rank);
            """
        )

    def _migration_3_add_multi_user_security(self) -> None:
        """Add authentication tables and private ownership to business data."""
        self._migration_2_add_persistence_contracts()
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_key TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_key TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL,
                email_normalized TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                password_iterations INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                failed_login_count INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT NOT NULL DEFAULT '',
                last_login_at TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tenant_memberships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL DEFAULT 'owner',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                UNIQUE (tenant_id, user_id),
                FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS auth_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_key TEXT NOT NULL UNIQUE,
                token_hash TEXT NOT NULL UNIQUE,
                tenant_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                revoked_at TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )

        ownership_columns = {
            "recruitment_projects": {
                "tenant_id": "INTEGER",
                "owner_user_id": "INTEGER",
            },
            "screening_sessions": {
                "tenant_id": "INTEGER",
                "created_by_user_id": "INTEGER",
            },
            "candidates": {
                "tenant_id": "INTEGER",
                "created_by_user_id": "INTEGER",
            },
            "resumes": {
                "tenant_id": "INTEGER",
                "created_by_user_id": "INTEGER",
            },
            "match_results": {
                "tenant_id": "INTEGER",
                "created_by_user_id": "INTEGER",
            },
        }
        for table_name, columns in ownership_columns.items():
            for column_name, definition in columns.items():
                self._ensure_column(table_name, column_name, definition)

        legacy_tenant_id, legacy_user_id = self._ensure_legacy_owner()

        self.connection.execute(
            """
            UPDATE recruitment_projects
            SET tenant_id = COALESCE(tenant_id, ?),
                owner_user_id = COALESCE(owner_user_id, ?)
            """,
            (legacy_tenant_id, legacy_user_id),
        )
        for table_name in (
            "screening_sessions",
            "candidates",
            "resumes",
            "match_results",
        ):
            self.connection.execute(
                f"""
                UPDATE {table_name}
                SET tenant_id = COALESCE(tenant_id, ?),
                    created_by_user_id = COALESCE(created_by_user_id, ?)
                """,
                (legacy_tenant_id, legacy_user_id),
            )

        self.connection.executescript(
            """
            DROP INDEX IF EXISTS ux_recruitment_projects_project_key;
            DROP INDEX IF EXISTS ux_screening_sessions_session_key;

            CREATE UNIQUE INDEX IF NOT EXISTS ux_projects_private_project_key
                ON recruitment_projects(tenant_id, owner_user_id, project_key)
                WHERE project_key IS NOT NULL AND project_key <> '';

            CREATE UNIQUE INDEX IF NOT EXISTS ux_sessions_tenant_session_key
                ON screening_sessions(tenant_id, session_key);

            CREATE UNIQUE INDEX IF NOT EXISTS ux_candidates_tenant_candidate_key
                ON candidates(tenant_id, candidate_key)
                WHERE candidate_key IS NOT NULL AND candidate_key <> '';

            CREATE INDEX IF NOT EXISTS ix_projects_private_scope
                ON recruitment_projects(tenant_id, owner_user_id, updated_at DESC);

            CREATE INDEX IF NOT EXISTS ix_sessions_private_scope
                ON screening_sessions(tenant_id, created_by_user_id, project_id, created_at DESC);

            CREATE INDEX IF NOT EXISTS ix_candidates_private_scope
                ON candidates(tenant_id, created_by_user_id, project_id, session_id);

            CREATE INDEX IF NOT EXISTS ix_matches_private_scope
                ON match_results(tenant_id, created_by_user_id, project_id, session_id, rank);

            CREATE INDEX IF NOT EXISTS ix_auth_sessions_lookup
                ON auth_sessions(token_hash, revoked_at, expires_at);
            """
        )

    def _migration_4_add_admin_provisioning_rbac(self) -> None:
        """Add employee-ID login, account lifecycle, RBAC, and admin audit data."""
        self._migration_3_add_multi_user_security()

        user_columns = {
            "employee_user_id": "TEXT NOT NULL DEFAULT ''",
            "employee_user_id_normalized": "TEXT NOT NULL DEFAULT ''",
            "country_location": "TEXT NOT NULL DEFAULT ''",
            "time_zone": "TEXT NOT NULL DEFAULT ''",
            "department": "TEXT NOT NULL DEFAULT ''",
            "business_unit": "TEXT NOT NULL DEFAULT ''",
            "manager_user_id": "TEXT NOT NULL DEFAULT ''",
            "role_code": "TEXT NOT NULL DEFAULT 'USER'",
            "account_status": "TEXT NOT NULL DEFAULT 'ACTIVE'",
            "must_change_password": "INTEGER NOT NULL DEFAULT 0",
            "temporary_password_expires_at": "TEXT NOT NULL DEFAULT ''",
            "password_changed_at": "TEXT NOT NULL DEFAULT ''",
            "valid_from": "TEXT NOT NULL DEFAULT ''",
            "valid_until": "TEXT NOT NULL DEFAULT ''",
            "created_by_user_id": "INTEGER",
            "updated_by_user_id": "INTEGER",
            "forgot_password_requested_at": "TEXT NOT NULL DEFAULT ''",
        }
        for column_name, definition in user_columns.items():
            self._ensure_column("users", column_name, definition)

        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_code TEXT NOT NULL UNIQUE,
                role_name TEXT NOT NULL,
                scope TEXT NOT NULL,
                is_system_role INTEGER NOT NULL DEFAULT 1,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                permission_code TEXT NOT NULL UNIQUE,
                permission_name TEXT NOT NULL,
                resource TEXT NOT NULL,
                action TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS role_permissions (
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                PRIMARY KEY (role_id, permission_id),
                FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
                FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS user_role_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                assigned_by_user_id INTEGER,
                status TEXT NOT NULL DEFAULT 'active',
                valid_from TEXT NOT NULL DEFAULT '',
                valid_until TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE (user_id, role_id, status),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT,
                FOREIGN KEY (assigned_by_user_id) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER,
                actor_user_id INTEGER,
                action TEXT NOT NULL,
                target_type TEXT NOT NULL DEFAULT '',
                target_id TEXT NOT NULL DEFAULT '',
                details_json TEXT NOT NULL DEFAULT '{}',
                outcome TEXT NOT NULL DEFAULT 'success',
                created_at TEXT NOT NULL,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE SET NULL,
                FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS password_reset_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                requested_user_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                requested_at TEXT NOT NULL,
                resolved_at TEXT NOT NULL DEFAULT '',
                resolved_by_user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                FOREIGN KEY (resolved_by_user_id) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS user_import_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uploaded_by_user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                total_rows INTEGER NOT NULL DEFAULT 0,
                created_rows INTEGER NOT NULL DEFAULT 0,
                skipped_rows INTEGER NOT NULL DEFAULT 0,
                failed_rows INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'completed',
                summary_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                FOREIGN KEY (uploaded_by_user_id) REFERENCES users(id) ON DELETE RESTRICT
            );
            """
        )

        now = self._utc_now()
        roles = (
            ("SYSTEM_OWNER", "System Owner", "global"),
            ("GLOBAL_ADMIN", "Global Admin", "global"),
            ("TENANT_ADMIN", "Tenant Admin", "location"),
            ("USER", "User", "private"),
            ("READER", "Reader", "shared"),
        )
        self.connection.executemany(
            """
            INSERT OR IGNORE INTO roles
            (role_code, role_name, scope, is_system_role, is_active, created_at, updated_at)
            VALUES (?, ?, ?, 1, 1, ?, ?)
            """,
            [(code, name, scope, now, now) for code, name, scope in roles],
        )

        permissions = (
            ("HOME_VIEW", "View home", "home", "read"),
            ("SCREENING_RUN", "Run screening", "screening", "create"),
            ("RESULTS_VIEW_OWN", "View own results", "results", "read"),
            ("CANDIDATES_VIEW_OWN", "View own candidates", "candidates", "read"),
            ("USER_MANAGE_GLOBAL", "Manage users globally", "users", "manage_global"),
            ("USER_MANAGE_TENANT", "Manage users in assigned location", "users", "manage_location"),
            ("ROLE_ASSIGN_GLOBAL", "Assign global roles", "roles", "assign_global"),
            ("ROLE_ASSIGN_TENANT", "Assign tenant roles", "roles", "assign_location"),
            ("USER_ACCESS_MASTER_EXPORT", "Export user access master", "users", "export"),
            ("SHARED_RECORDS_READ", "Read explicitly shared records", "sharing", "read"),
            ("SYSTEM_POLICY_MANAGE", "Manage system policy", "system", "manage"),
        )
        self.connection.executemany(
            """
            INSERT OR IGNORE INTO permissions
            (permission_code, permission_name, resource, action, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [(code, name, resource, action, now) for code, name, resource, action in permissions],
        )

        role_permissions = {
            "SYSTEM_OWNER": {item[0] for item in permissions},
            "GLOBAL_ADMIN": {
                "HOME_VIEW", "SCREENING_RUN", "RESULTS_VIEW_OWN", "CANDIDATES_VIEW_OWN",
                "USER_MANAGE_GLOBAL", "USER_MANAGE_TENANT", "ROLE_ASSIGN_TENANT",
                "USER_ACCESS_MASTER_EXPORT", "SHARED_RECORDS_READ",
            },
            "TENANT_ADMIN": {
                "HOME_VIEW", "SCREENING_RUN", "RESULTS_VIEW_OWN", "CANDIDATES_VIEW_OWN",
                "USER_MANAGE_TENANT", "ROLE_ASSIGN_TENANT",
                "USER_ACCESS_MASTER_EXPORT", "SHARED_RECORDS_READ",
            },
            "USER": {"HOME_VIEW", "SCREENING_RUN", "RESULTS_VIEW_OWN", "CANDIDATES_VIEW_OWN"},
            "READER": {"HOME_VIEW", "SHARED_RECORDS_READ"},
        }
        for role_code, permission_codes in role_permissions.items():
            role_row = self.connection.execute(
                "SELECT id FROM roles WHERE role_code = ?", (role_code,)
            ).fetchone()
            if not role_row:
                continue
            for permission_code in permission_codes:
                permission_row = self.connection.execute(
                    "SELECT id FROM permissions WHERE permission_code = ?",
                    (permission_code,),
                ).fetchone()
                if permission_row:
                    self.connection.execute(
                        "INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                        (int(role_row["id"]), int(permission_row["id"])),
                    )

        # Migrate existing self-registered users without exposing them or
        # creating duplicate employee IDs. The first existing active user is
        # treated as the initial System Owner; others become standard Users.
        rows = self.connection.execute(
            "SELECT id, user_key, email, status FROM users ORDER BY id"
        ).fetchall()
        active_owner_assigned = False
        for row in rows:
            database_user_id = int(row["id"])
            is_legacy = str(row["user_key"] or "") == self.LEGACY_USER_KEY
            is_active = str(row["status"] or "") == "active" and not is_legacy
            role_code = "USER"
            if is_legacy:
                role_code = "READER"
            elif is_active and not active_owner_assigned:
                role_code = "SYSTEM_OWNER"
                active_owner_assigned = True

            employee_id = "LEGACY" if is_legacy else f"U{database_user_id:06d}"
            account_status = "DISABLED" if not is_active else "ACTIVE"
            self.connection.execute(
                """
                UPDATE users
                SET employee_user_id = CASE
                        WHEN employee_user_id = '' THEN ? ELSE employee_user_id END,
                    employee_user_id_normalized = CASE
                        WHEN employee_user_id_normalized = '' THEN ? ELSE employee_user_id_normalized END,
                    country_location = CASE
                        WHEN country_location = '' THEN 'Unassigned' ELSE country_location END,
                    role_code = CASE
                        WHEN role_code = '' OR role_code = 'USER' THEN ? ELSE role_code END,
                    account_status = CASE
                        WHEN account_status = '' OR account_status = 'ACTIVE' THEN ? ELSE account_status END,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    employee_id,
                    employee_id.casefold(),
                    role_code,
                    account_status,
                    now,
                    database_user_id,
                ),
            )
            self.connection.execute(
                "UPDATE tenant_memberships SET role = ? WHERE user_id = ?",
                (role_code, database_user_id),
            )
            role_row = self.connection.execute(
                "SELECT id FROM roles WHERE role_code = ?", (role_code,)
            ).fetchone()
            if role_row:
                self.connection.execute(
                    """
                    INSERT OR IGNORE INTO user_role_assignments
                    (user_id, role_id, assigned_by_user_id, status, valid_from, valid_until,
                     created_at, updated_at)
                    VALUES (?, ?, NULL, 'active', '', '', ?, ?)
                    """,
                    (database_user_id, int(role_row["id"]), now, now),
                )

        self.connection.executescript(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_users_employee_user_id
                ON users(employee_user_id_normalized)
                WHERE employee_user_id_normalized <> '';

            CREATE INDEX IF NOT EXISTS ix_users_role_status
                ON users(role_code, account_status, country_location);

            CREATE INDEX IF NOT EXISTS ix_password_reset_requests_status
                ON password_reset_requests(status, requested_at DESC);

            CREATE INDEX IF NOT EXISTS ix_audit_events_actor_time
                ON audit_events(actor_user_id, created_at DESC);
            """
        )

    def _migration_5_add_tenant_configuration_versions(self) -> None:
        """Add immutable tenant configuration versions and screening snapshots."""
        self._migration_4_add_admin_provisioning_rbac()
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS tenant_configuration_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                configuration_key TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                source_name TEXT NOT NULL DEFAULT '',
                file_path TEXT NOT NULL,
                file_sha256 TEXT NOT NULL,
                file_size INTEGER NOT NULL DEFAULT 0,
                validation_json TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'DRAFT',
                created_by_user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                activated_by_user_id INTEGER,
                activated_at TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE RESTRICT,
                FOREIGN KEY (activated_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
                UNIQUE (tenant_id, version_number),
                UNIQUE (tenant_id, file_sha256)
            );

            CREATE INDEX IF NOT EXISTS ix_tenant_configuration_active
                ON tenant_configuration_versions(tenant_id, status, activated_at DESC);

            CREATE INDEX IF NOT EXISTS ix_tenant_configuration_created
                ON tenant_configuration_versions(tenant_id, created_at DESC);
            """
        )

        session_columns = {
            "configuration_version_id": "INTEGER",
            "configuration_sha256": "TEXT NOT NULL DEFAULT ''",
            "configuration_snapshot_json": "TEXT NOT NULL DEFAULT '{}'",
        }
        for column_name, definition in session_columns.items():
            self._ensure_column("screening_sessions", column_name, definition)

        now = self._utc_now()
        permissions = (
            (
                "CONFIGURATION_VIEW",
                "View active workspace configuration",
                "configuration",
                "read",
            ),
            (
                "CONFIGURATION_MANAGE_GLOBAL",
                "Manage configuration for any workspace",
                "configuration",
                "manage_global",
            ),
            (
                "CONFIGURATION_MANAGE_TENANT",
                "Manage configuration in assigned scope",
                "configuration",
                "manage_scope",
            ),
        )
        self.connection.executemany(
            """
            INSERT OR IGNORE INTO permissions
            (permission_code, permission_name, resource, action, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [(code, name, resource, action, now) for code, name, resource, action in permissions],
        )

        role_permissions = {
            "SYSTEM_OWNER": {
                "CONFIGURATION_VIEW",
                "CONFIGURATION_MANAGE_GLOBAL",
                "CONFIGURATION_MANAGE_TENANT",
            },
            "GLOBAL_ADMIN": {
                "CONFIGURATION_VIEW",
                "CONFIGURATION_MANAGE_GLOBAL",
                "CONFIGURATION_MANAGE_TENANT",
            },
            "TENANT_ADMIN": {
                "CONFIGURATION_VIEW",
                "CONFIGURATION_MANAGE_TENANT",
            },
            "USER": {"CONFIGURATION_VIEW"},
        }
        for role_code, permission_codes in role_permissions.items():
            role_row = self.connection.execute(
                "SELECT id FROM roles WHERE role_code = ?", (role_code,)
            ).fetchone()
            if not role_row:
                continue
            for permission_code in permission_codes:
                permission_row = self.connection.execute(
                    "SELECT id FROM permissions WHERE permission_code = ?",
                    (permission_code,),
                ).fetchone()
                if permission_row:
                    self.connection.execute(
                        "INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                        (int(role_row["id"]), int(permission_row["id"])),
                    )

    def _migration_6_add_explicit_record_sharing(self) -> None:
        """Add private-by-default project sharing and review assignments."""
        self._migration_5_add_tenant_configuration_versions()
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS record_shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_tenant_id INTEGER NOT NULL,
                owner_user_id INTEGER NOT NULL,
                grantee_user_id INTEGER NOT NULL,
                project_id INTEGER NOT NULL,
                access_role TEXT NOT NULL DEFAULT 'READER',
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                expires_at TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                review_status TEXT NOT NULL DEFAULT 'NOT_REQUIRED',
                review_note TEXT NOT NULL DEFAULT '',
                reviewed_at TEXT NOT NULL DEFAULT '',
                reviewed_by_user_id INTEGER,
                created_by_user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                revoked_by_user_id INTEGER,
                revoked_at TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (owner_tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
                FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (grantee_user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (project_id) REFERENCES recruitment_projects(id) ON DELETE CASCADE,
                FOREIGN KEY (reviewed_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
                FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE RESTRICT,
                FOREIGN KEY (revoked_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
                CHECK (access_role IN ('READER', 'REVIEWER')),
                CHECK (status IN ('ACTIVE', 'REVOKED', 'EXPIRED')),
                CHECK (review_status IN ('NOT_REQUIRED', 'ASSIGNED', 'IN_REVIEW', 'COMPLETED'))
            );

            CREATE UNIQUE INDEX IF NOT EXISTS ux_record_shares_active_assignment
                ON record_shares(project_id, grantee_user_id)
                WHERE status = 'ACTIVE';

            CREATE INDEX IF NOT EXISTS ix_record_shares_owner
                ON record_shares(owner_tenant_id, owner_user_id, project_id, created_at DESC);

            CREATE INDEX IF NOT EXISTS ix_record_shares_recipient
                ON record_shares(grantee_user_id, status, expires_at, created_at DESC);

            CREATE INDEX IF NOT EXISTS ix_record_shares_expiry
                ON record_shares(status, expires_at)
                WHERE status = 'ACTIVE' AND expires_at <> '';
            """
        )

        now = self._utc_now()
        self.connection.execute(
            """
            INSERT OR IGNORE INTO permissions
            (permission_code, permission_name, resource, action, created_at)
            VALUES ('SHARED_RECORDS_MANAGE_OWN',
                    'Share owned projects and revoke access',
                    'sharing', 'manage_own', ?)
            """,
            (now,),
        )

        role_permissions = {
            "SYSTEM_OWNER": {"SHARED_RECORDS_READ", "SHARED_RECORDS_MANAGE_OWN"},
            "GLOBAL_ADMIN": {"SHARED_RECORDS_READ", "SHARED_RECORDS_MANAGE_OWN"},
            "TENANT_ADMIN": {"SHARED_RECORDS_READ", "SHARED_RECORDS_MANAGE_OWN"},
            "USER": {"SHARED_RECORDS_READ", "SHARED_RECORDS_MANAGE_OWN"},
            "READER": {"SHARED_RECORDS_READ"},
        }
        for role_code, permission_codes in role_permissions.items():
            role_row = self.connection.execute(
                "SELECT id FROM roles WHERE role_code = ?",
                (role_code,),
            ).fetchone()
            if not role_row:
                continue
            for permission_code in permission_codes:
                permission_row = self.connection.execute(
                    "SELECT id FROM permissions WHERE permission_code = ?",
                    (permission_code,),
                ).fetchone()
                if permission_row:
                    self.connection.execute(
                        "INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                        (int(role_row["id"]), int(permission_row["id"])),
                    )

    def _migration_7_add_ai_provider_gateway(self) -> None:
        """Add provider/model/prompt registry, tenant policy, and safe telemetry."""
        self._migration_6_add_explicit_record_sharing()
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS ai_model_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_key TEXT NOT NULL UNIQUE,
                provider_code TEXT NOT NULL,
                model_name TEXT NOT NULL,
                display_name TEXT NOT NULL DEFAULT '',
                deployment_type TEXT NOT NULL,
                supports_structured_output INTEGER NOT NULL DEFAULT 1,
                input_cost_per_million_usd REAL NOT NULL DEFAULT 0,
                output_cost_per_million_usd REAL NOT NULL DEFAULT 0,
                context_window INTEGER NOT NULL DEFAULT 0,
                max_output_tokens INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                created_by_user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE RESTRICT,
                CHECK (provider_code IN ('OPENAI', 'OLLAMA')),
                CHECK (deployment_type IN ('HOSTED', 'LOCAL')),
                CHECK (status IN ('ACTIVE', 'INACTIVE')),
                CHECK (input_cost_per_million_usd >= 0),
                CHECK (output_cost_per_million_usd >= 0),
                CHECK (context_window >= 0),
                CHECK (max_output_tokens >= 0)
            );

            CREATE TABLE IF NOT EXISTS ai_prompt_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_key TEXT NOT NULL,
                task_code TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                system_template TEXT NOT NULL DEFAULT '',
                user_template TEXT NOT NULL,
                output_schema_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'DRAFT',
                created_by_user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                activated_by_user_id INTEGER,
                activated_at TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE RESTRICT,
                FOREIGN KEY (activated_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
                UNIQUE (prompt_key, version_number),
                CHECK (status IN ('DRAFT', 'ACTIVE', 'INACTIVE')),
                CHECK (version_number > 0)
            );

            CREATE TABLE IF NOT EXISTS tenant_ai_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                target_user_id INTEGER NOT NULL,
                task_code TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 0,
                model_id INTEGER NOT NULL,
                prompt_version_id INTEGER NOT NULL,
                allow_external_data INTEGER NOT NULL DEFAULT 0,
                max_input_chars INTEGER NOT NULL DEFAULT 120000,
                timeout_seconds INTEGER NOT NULL DEFAULT 60,
                daily_request_limit INTEGER NOT NULL DEFAULT 100,
                created_by_user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
                FOREIGN KEY (target_user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (model_id) REFERENCES ai_model_registry(id) ON DELETE RESTRICT,
                FOREIGN KEY (prompt_version_id) REFERENCES ai_prompt_versions(id) ON DELETE RESTRICT,
                FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE RESTRICT,
                UNIQUE (tenant_id, target_user_id, task_code),
                CHECK (enabled IN (0, 1)),
                CHECK (allow_external_data IN (0, 1)),
                CHECK (max_input_chars >= 1000),
                CHECK (timeout_seconds BETWEEN 5 AND 600),
                CHECK (daily_request_limit >= 1)
            );

            CREATE TABLE IF NOT EXISTS ai_inference_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                task_code TEXT NOT NULL,
                provider_code TEXT NOT NULL DEFAULT '',
                model_id INTEGER,
                model_key TEXT NOT NULL DEFAULT '',
                prompt_version_id INTEGER,
                request_id TEXT NOT NULL,
                outcome TEXT NOT NULL,
                latency_ms INTEGER NOT NULL DEFAULT 0,
                input_chars INTEGER NOT NULL DEFAULT 0,
                output_chars INTEGER NOT NULL DEFAULT 0,
                input_tokens INTEGER NOT NULL DEFAULT 0,
                output_tokens INTEGER NOT NULL DEFAULT 0,
                estimated_cost_usd REAL NOT NULL DEFAULT 0,
                error_code TEXT NOT NULL DEFAULT '',
                error_message_redacted TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (model_id) REFERENCES ai_model_registry(id) ON DELETE SET NULL,
                FOREIGN KEY (prompt_version_id) REFERENCES ai_prompt_versions(id) ON DELETE SET NULL,
                CHECK (outcome IN ('SUCCESS', 'ERROR', 'DENIED')),
                CHECK (latency_ms >= 0),
                CHECK (input_chars >= 0),
                CHECK (output_chars >= 0),
                CHECK (input_tokens >= 0),
                CHECK (output_tokens >= 0),
                CHECK (estimated_cost_usd >= 0)
            );

            CREATE INDEX IF NOT EXISTS ix_ai_model_provider_status
                ON ai_model_registry(provider_code, status, display_name);

            CREATE INDEX IF NOT EXISTS ix_ai_prompt_task_status
                ON ai_prompt_versions(task_code, status, prompt_key, version_number DESC);

            CREATE INDEX IF NOT EXISTS ix_tenant_ai_policy_target
                ON tenant_ai_policies(tenant_id, target_user_id, task_code);

            CREATE INDEX IF NOT EXISTS ix_ai_inference_user_time
                ON ai_inference_events(tenant_id, user_id, created_at DESC);

            CREATE INDEX IF NOT EXISTS ix_ai_inference_request
                ON ai_inference_events(request_id);
            """
        )

        now = self._utc_now()
        permissions = (
            (
                "AI_POLICY_VIEW",
                "View assigned AI model and prompt policy",
                "ai_policy",
                "read",
            ),
            (
                "AI_POLICY_MANAGE_GLOBAL",
                "Manage AI models, prompts, and policies globally",
                "ai_policy",
                "manage_global",
            ),
            (
                "AI_POLICY_MANAGE_TENANT",
                "Manage AI policies in assigned scope",
                "ai_policy",
                "manage_scope",
            ),
            (
                "AI_INFERENCE_RUN",
                "Run an enabled AI task through the provider gateway",
                "ai_inference",
                "execute",
            ),
        )
        self.connection.executemany(
            """
            INSERT OR IGNORE INTO permissions
            (permission_code, permission_name, resource, action, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [(code, name, resource, action, now) for code, name, resource, action in permissions],
        )

        role_permissions = {
            "SYSTEM_OWNER": {item[0] for item in permissions},
            "GLOBAL_ADMIN": {item[0] for item in permissions},
            "TENANT_ADMIN": {
                "AI_POLICY_VIEW",
                "AI_POLICY_MANAGE_TENANT",
                "AI_INFERENCE_RUN",
            },
            "USER": {"AI_POLICY_VIEW", "AI_INFERENCE_RUN"},
        }
        for role_code, permission_codes in role_permissions.items():
            role_row = self.connection.execute(
                "SELECT id FROM roles WHERE role_code = ?",
                (role_code,),
            ).fetchone()
            if not role_row:
                continue
            for permission_code in permission_codes:
                permission_row = self.connection.execute(
                    "SELECT id FROM permissions WHERE permission_code = ?",
                    (permission_code,),
                ).fetchone()
                if permission_row:
                    self.connection.execute(
                        "INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                        (int(role_row["id"]), int(permission_row["id"])),
                    )

    def _ensure_legacy_owner(self) -> tuple[int, int]:
        now = self._utc_now()
        self.connection.execute(
            """
            INSERT OR IGNORE INTO tenants
            (tenant_key, name, status, created_at, updated_at)
            VALUES (?, ?, 'disabled', ?, ?)
            """,
            (self.LEGACY_TENANT_KEY, "Legacy Imported Data", now, now),
        )
        tenant_row = self.connection.execute(
            "SELECT id FROM tenants WHERE tenant_key = ?",
            (self.LEGACY_TENANT_KEY,),
        ).fetchone()
        tenant_id = int(tenant_row["id"])

        self.connection.execute(
            """
            INSERT OR IGNORE INTO users
            (user_key, email, email_normalized, display_name, password_hash,
             password_salt, password_iterations, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, '!', '!', 100000, 'disabled', ?, ?)
            """,
            (
                self.LEGACY_USER_KEY,
                self.LEGACY_USER_EMAIL,
                self.LEGACY_USER_EMAIL,
                "Legacy Imported User",
                now,
                now,
            ),
        )
        user_row = self.connection.execute(
            "SELECT id FROM users WHERE user_key = ?",
            (self.LEGACY_USER_KEY,),
        ).fetchone()
        user_id = int(user_row["id"])

        self.connection.execute(
            """
            INSERT OR IGNORE INTO tenant_memberships
            (tenant_id, user_id, role, status, created_at)
            VALUES (?, ?, 'owner', 'disabled', ?)
            """,
            (tenant_id, user_id, now),
        )
        return tenant_id, user_id

    def _ensure_column(self, table_name: str, column_name: str, definition: str) -> None:
        if column_name in self.table_columns(table_name):
            return
        self.connection.execute(
            f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {definition}'
        )

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")
