"""Explicit project-sharing persistence with owner and recipient authorization."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from database.database import Database
from models.security_context import SecurityContext


class SharingRepository:
    """Persist project shares without weakening private owner repositories."""

    ACCESS_ROLES = {"READER", "REVIEWER"}
    REVIEW_STATUSES = {"ASSIGNED", "IN_REVIEW", "COMPLETED"}

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

    def grant_project_share(
        self,
        *,
        project_id: int,
        grantee_user_id: int,
        access_role: str,
        expires_at: str = "",
        note: str = "",
    ) -> dict[str, Any]:
        """Grant one active project share from the authenticated owner."""
        self._expire_due_shares()
        role = self._normalize_access_role(access_role)
        project = self._owned_project(project_id)
        if not project:
            raise PermissionError("Only the project owner can share this project.")

        grantee = self._active_user(grantee_user_id)
        if not grantee:
            raise LookupError("The selected recipient is not an active RecruitOS user.")
        if int(grantee_user_id) == int(self.context.user_id):
            raise ValueError("A project cannot be shared with its owner.")

        existing = self.db.connection.execute(
            """
            SELECT id FROM record_shares
            WHERE project_id = ? AND grantee_user_id = ? AND status = 'ACTIVE'
            LIMIT 1
            """,
            (int(project_id), int(grantee_user_id)),
        ).fetchone()
        if existing:
            raise ValueError("An active share already exists for this project and recipient.")

        now = self._utc_now()
        review_status = "ASSIGNED" if role == "REVIEWER" else "NOT_REQUIRED"
        with self.db.transaction():
            cursor = self.db.connection.execute(
                """
                INSERT INTO record_shares
                (owner_tenant_id, owner_user_id, grantee_user_id, project_id,
                 access_role, status, expires_at, note, review_status,
                 review_note, reviewed_at, reviewed_by_user_id,
                 created_by_user_id, created_at, updated_at,
                 revoked_by_user_id, revoked_at)
                VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?, '', '', NULL,
                        ?, ?, ?, NULL, '')
                """,
                (
                    int(self.context.tenant_id),
                    int(self.context.user_id),
                    int(grantee_user_id),
                    int(project_id),
                    role,
                    str(expires_at or ""),
                    str(note or "").strip(),
                    review_status,
                    int(self.context.user_id),
                    now,
                    now,
                ),
            )
            share_id = int(cursor.lastrowid)
            self._audit(
                tenant_id=self.context.tenant_id,
                actor_user_id=self.context.user_id,
                action="share.granted",
                share_id=share_id,
                details={
                    "project_id": int(project_id),
                    "grantee_user_id": int(grantee_user_id),
                    "access_role": role,
                    "expires_at": str(expires_at or ""),
                },
            )

        return self.get_owned_share(share_id) or {
            "id": share_id,
            "project_id": int(project_id),
        }

    def revoke_share(self, share_id: int) -> bool:
        """Revoke an active share only when the current user owns it."""
        self._expire_due_shares()
        row = self.db.connection.execute(
            """
            SELECT * FROM record_shares
            WHERE id = ? AND owner_tenant_id = ? AND owner_user_id = ?
              AND status = 'ACTIVE'
            """,
            (int(share_id), self.context.tenant_id, self.context.user_id),
        ).fetchone()
        if not row:
            return False

        now = self._utc_now()
        with self.db.transaction():
            cursor = self.db.connection.execute(
                """
                UPDATE record_shares
                SET status = 'REVOKED', revoked_by_user_id = ?, revoked_at = ?,
                    updated_at = ?
                WHERE id = ? AND owner_tenant_id = ? AND owner_user_id = ?
                  AND status = 'ACTIVE'
                """,
                (
                    self.context.user_id,
                    now,
                    now,
                    int(share_id),
                    self.context.tenant_id,
                    self.context.user_id,
                ),
            )
            if cursor.rowcount:
                self._audit(
                    tenant_id=self.context.tenant_id,
                    actor_user_id=self.context.user_id,
                    action="share.revoked",
                    share_id=int(share_id),
                    details={
                        "project_id": int(row["project_id"]),
                        "grantee_user_id": int(row["grantee_user_id"]),
                    },
                )
        return bool(cursor.rowcount)

    def update_review(
        self,
        share_id: int,
        *,
        review_status: str,
        review_note: str = "",
    ) -> dict[str, Any]:
        """Update reviewer progress without changing shared screening evidence."""
        self._expire_due_shares()
        status = str(review_status or "").strip().upper()
        if status not in self.REVIEW_STATUSES:
            raise ValueError("Unsupported review status.")

        share = self.get_received_share(share_id)
        if not share:
            raise PermissionError("The shared project is not available.")
        if str(share.get("access_role") or "") != "REVIEWER":
            raise PermissionError("Reader access cannot update reviewer progress.")

        now = self._utc_now()
        reviewed_at = now if status == "COMPLETED" else ""
        with self.db.transaction():
            self.db.connection.execute(
                """
                UPDATE record_shares
                SET review_status = ?, review_note = ?, reviewed_at = ?,
                    reviewed_by_user_id = ?, updated_at = ?
                WHERE id = ? AND grantee_user_id = ? AND status = 'ACTIVE'
                """,
                (
                    status,
                    str(review_note or "").strip(),
                    reviewed_at,
                    self.context.user_id,
                    now,
                    int(share_id),
                    self.context.user_id,
                ),
            )
            self._audit(
                tenant_id=int(share["owner_tenant_id"]),
                actor_user_id=self.context.user_id,
                action="share.review_updated",
                share_id=int(share_id),
                details={
                    "project_id": int(share["project_id"]),
                    "review_status": status,
                },
            )
        refreshed = self.get_received_share(share_id)
        if not refreshed:
            raise LookupError("The reviewer assignment is no longer available.")
        return refreshed

    def get_owned_share(self, share_id: int) -> dict[str, Any] | None:
        self._expire_due_shares()
        row = self.db.connection.execute(
            self._owned_select() + " AND rs.id = ?",
            (self.context.tenant_id, self.context.user_id, int(share_id)),
        ).fetchone()
        return dict(row) if row else None

    def list_owned_shares(
        self,
        *,
        project_id: int | None = None,
    ) -> list[dict[str, Any]]:
        self._expire_due_shares()
        params: list[Any] = [self.context.tenant_id, self.context.user_id]
        clause = ""
        if project_id is not None:
            clause = " AND rs.project_id = ?"
            params.append(int(project_id))
        rows = self.db.connection.execute(
            self._owned_select() + clause + " ORDER BY rs.created_at DESC, rs.id DESC",
            tuple(params),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_received_share(self, share_id: int) -> dict[str, Any] | None:
        self._expire_due_shares()
        row = self.db.connection.execute(
            self._received_select() + " AND rs.id = ?",
            (self.context.user_id, int(share_id)),
        ).fetchone()
        return dict(row) if row else None

    def list_received_shares(self) -> list[dict[str, Any]]:
        self._expire_due_shares()
        rows = self.db.connection.execute(
            self._received_select() + " ORDER BY rs.created_at DESC, rs.id DESC",
            (self.context.user_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_received_sessions(self, share_id: int) -> list[dict[str, Any]]:
        share = self.get_received_share(share_id)
        if not share:
            raise PermissionError("The shared project is not available.")
        rows = self.db.connection.execute(
            """
            SELECT s.id, s.session_key, s.resumes_requested, s.resumes_processed,
                   s.resumes_failed, s.shortlisted_count, s.status, s.created_at,
                   s.configuration_version_id, s.configuration_sha256
            FROM screening_sessions s
            WHERE s.project_id = ? AND s.tenant_id = ? AND s.created_by_user_id = ?
            ORDER BY s.created_at DESC, s.id DESC
            """,
            (
                int(share["project_id"]),
                int(share["owner_tenant_id"]),
                int(share["owner_user_id"]),
            ),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_share_audit(self, share_id: int) -> list[dict[str, Any]]:
        """Return audit history only to the share owner or recipient."""
        accessible = self.db.connection.execute(
            """
            SELECT 1 FROM record_shares
            WHERE id = ? AND (owner_user_id = ? OR grantee_user_id = ?)
            """,
            (int(share_id), self.context.user_id, self.context.user_id),
        ).fetchone()
        if not accessible:
            raise PermissionError("The sharing audit history is not available.")
        rows = self.db.connection.execute(
            """
            SELECT id, actor_user_id, action, details_json, outcome, created_at
            FROM audit_events
            WHERE target_type = 'record_share' AND target_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (str(int(share_id)),),
        ).fetchall()
        return [dict(row) for row in rows]

    def close(self) -> None:
        if self._owns_database:
            self.db.close()

    def _owned_project(self, project_id: int) -> dict[str, Any] | None:
        row = self.db.connection.execute(
            """
            SELECT * FROM recruitment_projects
            WHERE id = ? AND tenant_id = ? AND owner_user_id = ?
            """,
            (int(project_id), self.context.tenant_id, self.context.user_id),
        ).fetchone()
        return dict(row) if row else None

    def _active_user(self, user_id: int) -> dict[str, Any] | None:
        row = self.db.connection.execute(
            """
            SELECT id, employee_user_id, display_name, email, role_code,
                   country_location, account_status, status
            FROM users
            WHERE id = ? AND status = 'active'
              AND account_status IN ('ACTIVE', 'RESET_REQUIRED')
            """,
            (int(user_id),),
        ).fetchone()
        return dict(row) if row else None

    def _expire_due_shares(self) -> int:
        now = self._utc_now()
        rows = self.db.connection.execute(
            """
            SELECT id, owner_tenant_id, owner_user_id, grantee_user_id, project_id
            FROM record_shares
            WHERE status = 'ACTIVE' AND expires_at <> '' AND expires_at <= ?
            """,
            (now,),
        ).fetchall()
        if not rows:
            return 0
        with self.db.transaction():
            for row in rows:
                self.db.connection.execute(
                    """
                    UPDATE record_shares
                    SET status = 'EXPIRED', updated_at = ?
                    WHERE id = ? AND status = 'ACTIVE'
                    """,
                    (now, int(row["id"])),
                )
                self._audit(
                    tenant_id=int(row["owner_tenant_id"]),
                    actor_user_id=None,
                    action="share.expired",
                    share_id=int(row["id"]),
                    details={
                        "project_id": int(row["project_id"]),
                        "grantee_user_id": int(row["grantee_user_id"]),
                    },
                )
        return len(rows)

    def _audit(
        self,
        *,
        tenant_id: int,
        actor_user_id: int | None,
        action: str,
        share_id: int,
        details: dict[str, Any],
    ) -> None:
        self.db.connection.execute(
            """
            INSERT INTO audit_events
            (tenant_id, actor_user_id, action, target_type, target_id,
             details_json, outcome, created_at)
            VALUES (?, ?, ?, 'record_share', ?, ?, 'success', ?)
            """,
            (
                int(tenant_id),
                actor_user_id,
                str(action),
                str(int(share_id)),
                json.dumps(details, ensure_ascii=False),
                self._utc_now(),
            ),
        )

    @staticmethod
    def _normalize_access_role(access_role: str) -> str:
        role = str(access_role or "").strip().upper()
        if role not in SharingRepository.ACCESS_ROLES:
            raise ValueError("Access role must be Reader or Reviewer.")
        return role

    @staticmethod
    def _owned_select() -> str:
        return """
            SELECT rs.*, p.project_name, p.client_name, p.job_id, p.job_title,
                   p.status AS project_status,
                   u.employee_user_id AS grantee_login_id,
                   u.display_name AS grantee_name,
                   u.email AS grantee_email,
                   u.role_code AS grantee_role,
                   u.country_location AS grantee_country_location
            FROM record_shares rs
            JOIN recruitment_projects p
              ON p.id = rs.project_id
             AND p.tenant_id = rs.owner_tenant_id
             AND p.owner_user_id = rs.owner_user_id
            JOIN users u ON u.id = rs.grantee_user_id
            WHERE rs.owner_tenant_id = ? AND rs.owner_user_id = ?
        """

    @staticmethod
    def _received_select() -> str:
        return """
            SELECT rs.*, p.project_name, p.client_name, p.job_id, p.job_title,
                   p.status AS project_status,
                   owner.employee_user_id AS owner_login_id,
                   owner.display_name AS owner_name,
                   owner.email AS owner_email,
                   owner.country_location AS owner_country_location
            FROM record_shares rs
            JOIN recruitment_projects p
              ON p.id = rs.project_id
             AND p.tenant_id = rs.owner_tenant_id
             AND p.owner_user_id = rs.owner_user_id
            JOIN users owner ON owner.id = rs.owner_user_id
            WHERE rs.grantee_user_id = ? AND rs.status = 'ACTIVE'
              AND owner.status = 'active'
              AND owner.account_status IN ('ACTIVE', 'RESET_REQUIRED')
        """

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")
