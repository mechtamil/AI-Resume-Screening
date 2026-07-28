"""Explicit one-time transfer of pre-multi-user data to a private workspace."""
from __future__ import annotations

from pathlib import Path

from database.database import Database
from database.user_repository import UserRepository
from services.auth_service import AuthService


class LegacyDataService:
    """Claim disabled legacy-owned records after an explicit administrator action."""

    @classmethod
    def claim_for_user(
        cls,
        employee_user_id: str,
        database_path: str | Path | None = None,
    ) -> dict[str, int]:
        """Transfer all legacy-owned records to one explicit active User ID."""
        database = Database(database_path)
        database.create_tables()
        users = UserRepository(database)
        try:
            target = users.get_user_by_login_id(
                AuthService.normalize_user_id(employee_user_id)
            )
            if not target or str(target.get("status") or "") != "active":
                raise LookupError(
                    "An active RecruitOS account was not found for this User ID."
                )

            legacy_tenant = database.connection.execute(
                "SELECT id FROM tenants WHERE tenant_key = ?",
                (Database.LEGACY_TENANT_KEY,),
            ).fetchone()
            legacy_user = database.connection.execute(
                "SELECT id FROM users WHERE user_key = ?",
                (Database.LEGACY_USER_KEY,),
            ).fetchone()
            if not legacy_tenant or not legacy_user:
                return cls._empty_result()

            legacy_tenant_id = int(legacy_tenant["id"])
            legacy_user_id = int(legacy_user["id"])
            target_tenant_id = int(target["tenant_id"])
            target_user_id = int(target["id"])

            cls._make_project_keys_safe(
                database,
                legacy_tenant_id=legacy_tenant_id,
                legacy_user_id=legacy_user_id,
                target_tenant_id=target_tenant_id,
                target_user_id=target_user_id,
            )

            counts: dict[str, int] = {}
            with database.transaction():
                cursor = database.connection.execute(
                    """
                    UPDATE recruitment_projects
                    SET tenant_id = ?, owner_user_id = ?
                    WHERE tenant_id = ? AND owner_user_id = ?
                    """,
                    (
                        target_tenant_id,
                        target_user_id,
                        legacy_tenant_id,
                        legacy_user_id,
                    ),
                )
                counts["projects"] = cursor.rowcount

                for table_name, result_key in (
                    ("screening_sessions", "sessions"),
                    ("candidates", "candidates"),
                    ("resumes", "resumes"),
                    ("match_results", "match_results"),
                ):
                    cursor = database.connection.execute(
                        f"""
                        UPDATE {table_name}
                        SET tenant_id = ?, created_by_user_id = ?
                        WHERE tenant_id = ? AND created_by_user_id = ?
                        """,
                        (
                            target_tenant_id,
                            target_user_id,
                            legacy_tenant_id,
                            legacy_user_id,
                        ),
                    )
                    counts[result_key] = cursor.rowcount

            users.audit_event(
                tenant_id=target_tenant_id,
                actor_user_id=target_user_id,
                action="LEGACY_DATA_CLAIMED",
                target_type="user",
                target_id=str(target_user_id),
                details=counts,
            )
            return counts
        finally:
            users.close()
            database.close()

    @staticmethod
    def _make_project_keys_safe(
        database: Database,
        *,
        legacy_tenant_id: int,
        legacy_user_id: int,
        target_tenant_id: int,
        target_user_id: int,
    ) -> None:
        legacy_projects = database.connection.execute(
            """
            SELECT id, project_key
            FROM recruitment_projects
            WHERE tenant_id = ? AND owner_user_id = ?
            """,
            (legacy_tenant_id, legacy_user_id),
        ).fetchall()

        for project in legacy_projects:
            key = str(project["project_key"] or "").strip()
            if not key:
                continue
            conflict = database.connection.execute(
                """
                SELECT 1 FROM recruitment_projects
                WHERE tenant_id = ? AND owner_user_id = ? AND project_key = ?
                """,
                (target_tenant_id, target_user_id, key),
            ).fetchone()
            if conflict:
                database.connection.execute(
                    """
                    UPDATE recruitment_projects
                    SET project_key = ?
                    WHERE id = ? AND tenant_id = ? AND owner_user_id = ?
                    """,
                    (
                        f"legacy:{int(project['id'])}:{key}",
                        int(project["id"]),
                        legacy_tenant_id,
                        legacy_user_id,
                    ),
                )

    @staticmethod
    def _empty_result() -> dict[str, int]:
        return {
            "projects": 0,
            "sessions": 0,
            "candidates": 0,
            "resumes": 0,
            "match_results": 0,
        }
