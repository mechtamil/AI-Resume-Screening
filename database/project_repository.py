"""Private recruitment-project persistence repository."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from database.database import Database
from models.recruitment_project import RecruitmentProject
from models.security_context import SecurityContext


class ProjectRepository:
    """Persist projects visible only to the authenticated owner."""

    def __init__(
        self,
        context: SecurityContext,
        database: Database | str | Path | None = None,
    ) -> None:
        context.require_valid()
        self.context = context
        self._owns_database = not isinstance(database, Database)
        self.db = database if isinstance(database, Database) else Database(database)
        self.db.create_tables()

    def upsert_project(
        self,
        project: RecruitmentProject,
        *,
        project_key: str = "",
        job_id: str = "",
        job_description: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> int:
        now = self._utc_now()
        key = str(project_key or "").strip() or uuid4().hex
        payload = json.dumps(job_description or {}, ensure_ascii=False)

        existing = self.db.connection.execute(
            """
            SELECT id
            FROM recruitment_projects
            WHERE tenant_id = ? AND owner_user_id = ? AND project_key = ?
            """,
            (self.context.tenant_id, self.context.user_id, key),
        ).fetchone()

        if existing:
            project_id = int(existing["id"])
            self.db.connection.execute(
                """
                UPDATE recruitment_projects
                SET project_name = ?, client_name = ?, job_id = ?, job_title = ?,
                    hiring_manager = ?, location = ?, target_headcount = ?,
                    status = ?, jd_json = ?, updated_at = ?
                WHERE id = ? AND tenant_id = ? AND owner_user_id = ?
                """,
                (
                    project.project_name,
                    project.client_name,
                    job_id,
                    project.job_title,
                    project.hiring_manager,
                    project.location,
                    int(project.target_headcount or 0),
                    project.status,
                    payload,
                    now,
                    project_id,
                    self.context.tenant_id,
                    self.context.user_id,
                ),
            )
        else:
            cursor = self.db.connection.execute(
                """
                INSERT INTO recruitment_projects
                (tenant_id, owner_user_id, project_key, project_name,
                 client_name, job_id, job_title, hiring_manager, location,
                 target_headcount, status, jd_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.context.tenant_id,
                    self.context.user_id,
                    key,
                    project.project_name,
                    project.client_name,
                    job_id,
                    project.job_title,
                    project.hiring_manager,
                    project.location,
                    int(project.target_headcount or 0),
                    project.status,
                    payload,
                    now,
                    now,
                ),
            )
            project_id = int(cursor.lastrowid)

        if commit:
            self.db.connection.commit()
        return project_id

    def get_project(self, project_id: int) -> dict[str, Any] | None:
        row = self.db.connection.execute(
            """
            SELECT *
            FROM recruitment_projects
            WHERE id = ? AND tenant_id = ? AND owner_user_id = ?
            """,
            (int(project_id), self.context.tenant_id, self.context.user_id),
        ).fetchone()
        return dict(row) if row else None

    def get_project_by_key(self, project_key: str) -> dict[str, Any] | None:
        row = self.db.connection.execute(
            """
            SELECT *
            FROM recruitment_projects
            WHERE project_key = ? AND tenant_id = ? AND owner_user_id = ?
            """,
            (
                str(project_key or "").strip(),
                self.context.tenant_id,
                self.context.user_id,
            ),
        ).fetchone()
        return dict(row) if row else None

    def list_projects(self) -> list[dict[str, Any]]:
        rows = self.db.connection.execute(
            """
            SELECT
                p.*,
                COUNT(DISTINCT s.id) AS screening_sessions,
                COUNT(DISTINCT c.id) AS candidates,
                COUNT(DISTINCT CASE WHEN m.shortlisted = 1 THEN m.id END)
                    AS shortlisted
            FROM recruitment_projects p
            LEFT JOIN screening_sessions s
              ON s.project_id = p.id
             AND s.tenant_id = p.tenant_id
             AND s.created_by_user_id = p.owner_user_id
            LEFT JOIN candidates c
              ON c.project_id = p.id
             AND c.tenant_id = p.tenant_id
             AND c.created_by_user_id = p.owner_user_id
            LEFT JOIN match_results m
              ON m.project_id = p.id
             AND m.tenant_id = p.tenant_id
             AND m.created_by_user_id = p.owner_user_id
            WHERE p.tenant_id = ? AND p.owner_user_id = ?
            GROUP BY p.id
            ORDER BY p.updated_at DESC, p.id DESC
            """,
            (self.context.tenant_id, self.context.user_id),
        ).fetchall()
        return [dict(row) for row in rows]

    def delete_project(self, project_id: int, *, commit: bool = True) -> bool:
        cursor = self.db.connection.execute(
            """
            DELETE FROM recruitment_projects
            WHERE id = ? AND tenant_id = ? AND owner_user_id = ?
            """,
            (int(project_id), self.context.tenant_id, self.context.user_id),
        )
        if commit:
            self.db.connection.commit()
        return cursor.rowcount > 0

    def close(self) -> None:
        if self._owns_database:
            self.db.close()

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")
