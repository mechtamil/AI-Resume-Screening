"""User, RBAC, audit, and authentication-session persistence."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from database.database import Database


class UserRepository:
    """Persistence layer for RecruitOS identities and admin operations."""

    def __init__(self, database: Database | str | Path | None = None) -> None:
        self._owns_database = not isinstance(database, Database)
        self.db = database if isinstance(database, Database) else Database(database)
        self.db.create_tables()

    # ------------------------------------------------------------------
    # Provisioning
    # ------------------------------------------------------------------

    def has_system_owner(self) -> bool:
        row = self.db.connection.execute(
            """
            SELECT 1
            FROM users
            WHERE role_code = 'SYSTEM_OWNER'
              AND status = 'active'
              AND account_status IN ('ACTIVE', 'RESET_REQUIRED')
            LIMIT 1
            """
        ).fetchone()
        return row is not None

    def create_system_owner(
        self,
        *,
        employee_user_id: str,
        display_name: str,
        email: str,
        country_location: str,
        password_hash: str,
        password_salt: str,
        password_iterations: int,
    ) -> dict[str, int | str]:
        if self.has_system_owner():
            raise PermissionError("The RecruitOS System Owner has already been configured.")
        return self.create_provisioned_user(
            employee_user_id=employee_user_id,
            display_name=display_name,
            email=email,
            country_location=country_location,
            role_code="SYSTEM_OWNER",
            password_hash=password_hash,
            password_salt=password_salt,
            password_iterations=password_iterations,
            account_status="ACTIVE",
            must_change_password=False,
            temporary_password_expires_at="",
            created_by_user_id=None,
        )

    def create_provisioned_user(
        self,
        *,
        employee_user_id: str,
        display_name: str,
        email: str,
        country_location: str,
        role_code: str,
        password_hash: str,
        password_salt: str,
        password_iterations: int,
        account_status: str = "RESET_REQUIRED",
        must_change_password: bool = True,
        temporary_password_expires_at: str = "",
        time_zone: str = "",
        department: str = "",
        business_unit: str = "",
        manager_user_id: str = "",
        valid_from: str = "",
        valid_until: str = "",
        created_by_user_id: int | None = None,
    ) -> dict[str, int | str | bool]:
        now = self._utc_now()
        login_id = str(employee_user_id or "").strip()
        login_id_normalized = login_id.casefold()
        email_value = str(email or "").strip()
        email_normalized = email_value.casefold()
        display_value = str(display_name or "").strip()
        role_value = str(role_code or "").strip().upper()
        country_value = str(country_location or "").strip()
        account_status_value = str(account_status or "RESET_REQUIRED").strip().upper()
        if account_status_value not in {
            "PENDING_ACTIVATION",
            "RESET_REQUIRED",
            "ACTIVE",
            "LOCKED",
            "DISABLED",
            "EXPIRED",
        }:
            raise ValueError("Unsupported account status.")
        legacy_status = (
            "disabled"
            if account_status_value in {"DISABLED", "EXPIRED"}
            else "active"
        )
        tenant_key = uuid4().hex
        user_key = uuid4().hex

        role_row = self.db.connection.execute(
            "SELECT id FROM roles WHERE role_code = ? AND is_active = 1",
            (role_value,),
        ).fetchone()
        if not role_row:
            raise ValueError(f"Role {role_value!r} is not active in RecruitOS.")

        try:
            with self.db.transaction():
                tenant_cursor = self.db.connection.execute(
                    """
                    INSERT INTO tenants
                    (tenant_key, name, status, created_at, updated_at)
                    VALUES (?, ?, 'active', ?, ?)
                    """,
                    (tenant_key, f"{display_value} Private Workspace", now, now),
                )
                tenant_id = int(tenant_cursor.lastrowid)

                user_cursor = self.db.connection.execute(
                    """
                    INSERT INTO users
                    (user_key, email, email_normalized, display_name,
                     password_hash, password_salt, password_iterations,
                     status, failed_login_count, locked_until, last_login_at,
                     created_at, updated_at,
                     employee_user_id, employee_user_id_normalized,
                     country_location, time_zone, department, business_unit,
                     manager_user_id, role_code, account_status,
                     must_change_password, temporary_password_expires_at,
                     password_changed_at, valid_from, valid_until,
                     created_by_user_id, updated_by_user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?,
                            ?, 0, '', '', ?, ?,
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', ?, ?, ?, ?)
                    """,
                    (
                        user_key,
                        email_value,
                        email_normalized,
                        display_value,
                        password_hash,
                        password_salt,
                        int(password_iterations),
                        legacy_status,
                        now,
                        now,
                        login_id,
                        login_id_normalized,
                        country_value,
                        str(time_zone or "").strip(),
                        str(department or "").strip(),
                        str(business_unit or "").strip(),
                        str(manager_user_id or "").strip(),
                        role_value,
                        account_status_value,
                        int(bool(must_change_password)),
                        str(temporary_password_expires_at or ""),
                        str(valid_from or ""),
                        str(valid_until or ""),
                        created_by_user_id,
                        created_by_user_id,
                    ),
                )
                database_user_id = int(user_cursor.lastrowid)

                self.db.connection.execute(
                    """
                    INSERT INTO tenant_memberships
                    (tenant_id, user_id, role, status, created_at)
                    VALUES (?, ?, ?, 'active', ?)
                    """,
                    (tenant_id, database_user_id, role_value, now),
                )
                self.db.connection.execute(
                    """
                    INSERT INTO user_role_assignments
                    (user_id, role_id, assigned_by_user_id, status,
                     valid_from, valid_until, created_at, updated_at)
                    VALUES (?, ?, ?, 'active', ?, ?, ?, ?)
                    """,
                    (
                        database_user_id,
                        int(role_row["id"]),
                        created_by_user_id,
                        str(valid_from or ""),
                        str(valid_until or ""),
                        now,
                        now,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            message = str(exc)
            if "employee_user_id_normalized" in message:
                raise ValueError("This User ID already exists in RecruitOS.") from exc
            if "email_normalized" in message:
                raise ValueError("An account already exists for this email address.") from exc
            raise

        return {
            "tenant_id": tenant_id,
            "tenant_key": tenant_key,
            "user_id": database_user_id,
            "user_key": user_key,
            "employee_user_id": login_id,
            "email": email_value,
            "display_name": display_value,
            "country_location": country_value,
            "role": role_value,
            "account_status": account_status_value,
            "must_change_password": bool(must_change_password),
            "temporary_password_expires_at": str(temporary_password_expires_at or ""),
        }

    # ------------------------------------------------------------------
    # Lookups and admin lists
    # ------------------------------------------------------------------

    def get_user_by_login_id(self, employee_user_id: str) -> dict[str, Any] | None:
        row = self.db.connection.execute(
            """
            SELECT u.*, tm.tenant_id, tm.role AS membership_role,
                   tm.status AS membership_status, t.status AS tenant_status
            FROM users u
            JOIN tenant_memberships tm ON tm.user_id = u.id
            JOIN tenants t ON t.id = tm.tenant_id
            WHERE u.employee_user_id_normalized = ?
            ORDER BY tm.id ASC
            LIMIT 1
            """,
            (str(employee_user_id or "").strip().casefold(),),
        ).fetchone()
        return dict(row) if row else None

    def get_user_by_email(self, email_normalized: str) -> dict[str, Any] | None:
        row = self.db.connection.execute(
            """
            SELECT u.*, tm.tenant_id, tm.role AS membership_role,
                   tm.status AS membership_status, t.status AS tenant_status
            FROM users u
            JOIN tenant_memberships tm ON tm.user_id = u.id
            JOIN tenants t ON t.id = tm.tenant_id
            WHERE u.email_normalized = ?
            ORDER BY tm.id ASC
            LIMIT 1
            """,
            (str(email_normalized or "").strip().casefold(),),
        ).fetchone()
        return dict(row) if row else None

    def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        row = self.db.connection.execute(
            """
            SELECT u.*, tm.tenant_id, tm.role AS membership_role,
                   tm.status AS membership_status, t.status AS tenant_status
            FROM users u
            JOIN tenant_memberships tm ON tm.user_id = u.id
            JOIN tenants t ON t.id = tm.tenant_id
            WHERE u.id = ?
            ORDER BY tm.id ASC
            LIMIT 1
            """,
            (int(user_id),),
        ).fetchone()
        return dict(row) if row else None

    def list_users(
        self,
        *,
        country_location: str | None = None,
        include_disabled: bool = True,
    ) -> list[dict[str, Any]]:
        conditions = ["u.user_key <> ?"]
        params: list[Any] = [Database.LEGACY_USER_KEY]
        if country_location is not None:
            conditions.append("LOWER(u.country_location) = LOWER(?)")
            params.append(str(country_location))
        if not include_disabled:
            conditions.append("u.account_status <> 'DISABLED'")
        rows = self.db.connection.execute(
            f"""
            SELECT u.id, u.employee_user_id, u.display_name, u.email,
                   u.country_location, u.time_zone, u.department, u.business_unit,
                   u.manager_user_id, u.role_code, u.account_status,
                   u.must_change_password, u.temporary_password_expires_at,
                   u.valid_from, u.valid_until, u.last_login_at,
                   u.failed_login_count, u.locked_until,
                   u.created_by_user_id, u.created_at, u.updated_at
            FROM users u
            WHERE {' AND '.join(conditions)}
            ORDER BY u.display_name COLLATE NOCASE, u.employee_user_id
            """,
            tuple(params),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_roles(self) -> list[dict[str, Any]]:
        rows = self.db.connection.execute(
            """
            SELECT role_code, role_name, scope, is_active
            FROM roles
            ORDER BY id
            """
        ).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Credential and account lifecycle
    # ------------------------------------------------------------------

    def update_password(
        self,
        user_id: int,
        *,
        password_hash: str,
        password_salt: str,
        password_iterations: int,
        account_status: str = "ACTIVE",
        must_change_password: bool = False,
        temporary_password_expires_at: str = "",
        updated_by_user_id: int | None = None,
    ) -> None:
        now = self._utc_now()
        self.db.connection.execute(
            """
            UPDATE users
            SET password_hash = ?, password_salt = ?, password_iterations = ?,
                account_status = ?, must_change_password = ?,
                temporary_password_expires_at = ?, password_changed_at = ?,
                failed_login_count = 0, locked_until = '',
                updated_by_user_id = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                password_hash,
                password_salt,
                int(password_iterations),
                str(account_status).upper(),
                int(bool(must_change_password)),
                str(temporary_password_expires_at or ""),
                now,
                updated_by_user_id,
                now,
                int(user_id),
            ),
        )
        self.db.connection.commit()

    def update_user_role(
        self,
        user_id: int,
        *,
        role_code: str,
        assigned_by_user_id: int,
    ) -> None:
        role_value = str(role_code or "").upper()
        role_row = self.db.connection.execute(
            "SELECT id FROM roles WHERE role_code = ? AND is_active = 1",
            (role_value,),
        ).fetchone()
        if not role_row:
            raise ValueError("The selected role is not active.")
        now = self._utc_now()
        with self.db.transaction():
            self.db.connection.execute(
                "UPDATE users SET role_code = ?, updated_by_user_id = ?, updated_at = ? WHERE id = ?",
                (role_value, int(assigned_by_user_id), now, int(user_id)),
            )
            self.db.connection.execute(
                "UPDATE tenant_memberships SET role = ? WHERE user_id = ?",
                (role_value, int(user_id)),
            )
            self.db.connection.execute(
                "UPDATE user_role_assignments SET status = 'inactive', updated_at = ? WHERE user_id = ? AND status = 'active'",
                (now, int(user_id)),
            )
            self.db.connection.execute(
                """
                INSERT INTO user_role_assignments
                (user_id, role_id, assigned_by_user_id, status,
                 valid_from, valid_until, created_at, updated_at)
                VALUES (?, ?, ?, 'active', '', '', ?, ?)
                """,
                (int(user_id), int(role_row["id"]), int(assigned_by_user_id), now, now),
            )

    def update_account_status(
        self,
        user_id: int,
        *,
        account_status: str,
        updated_by_user_id: int,
    ) -> None:
        status_value = str(account_status or "").upper()
        if status_value not in {
            "PENDING_ACTIVATION",
            "RESET_REQUIRED",
            "ACTIVE",
            "LOCKED",
            "DISABLED",
            "EXPIRED",
        }:
            raise ValueError("Unsupported account status.")
        legacy_status = "disabled" if status_value in {"DISABLED", "EXPIRED"} else "active"
        now = self._utc_now()
        self.db.connection.execute(
            """
            UPDATE users
            SET account_status = ?, status = ?, updated_by_user_id = ?, updated_at = ?
            WHERE id = ?
            """,
            (status_value, legacy_status, int(updated_by_user_id), now, int(user_id)),
        )
        if status_value in {"DISABLED", "EXPIRED"}:
            self.revoke_all_sessions_for_user(int(user_id), commit=False)
        self.db.connection.commit()

    def record_failed_login(
        self,
        user_id: int,
        *,
        failed_count: int,
        locked_until: str = "",
    ) -> None:
        self.db.connection.execute(
            """
            UPDATE users
            SET failed_login_count = ?, locked_until = ?, updated_at = ?
            WHERE id = ?
            """,
            (int(failed_count), str(locked_until or ""), self._utc_now(), int(user_id)),
        )
        self.db.connection.commit()

    def record_successful_login(self, user_id: int) -> None:
        now = self._utc_now()
        self.db.connection.execute(
            """
            UPDATE users
            SET failed_login_count = 0, locked_until = '',
                last_login_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (now, now, int(user_id)),
        )
        self.db.connection.commit()

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def create_auth_session(
        self,
        *,
        user_id: int,
        tenant_id: int,
        token_hash: str,
        expires_at: str,
    ) -> str:
        now = self._utc_now()
        session_key = uuid4().hex
        self.db.connection.execute(
            """
            INSERT INTO auth_sessions
            (session_key, token_hash, tenant_id, user_id, created_at,
             expires_at, last_seen_at, revoked_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, '')
            """,
            (session_key, str(token_hash), int(tenant_id), int(user_id), now, str(expires_at), now),
        )
        self.db.connection.commit()
        return session_key

    def get_active_session(self, token_hash: str, *, now: str) -> dict[str, Any] | None:
        row = self.db.connection.execute(
            """
            SELECT s.session_key, s.tenant_id, s.user_id, s.expires_at,
                   u.email, u.display_name, u.employee_user_id,
                   u.country_location, u.role_code, u.account_status,
                   u.must_change_password, u.status AS user_status,
                   tm.status AS membership_status, t.status AS tenant_status
            FROM auth_sessions s
            JOIN users u ON u.id = s.user_id
            JOIN tenant_memberships tm
              ON tm.user_id = s.user_id AND tm.tenant_id = s.tenant_id
            JOIN tenants t ON t.id = s.tenant_id
            WHERE s.token_hash = ?
              AND s.revoked_at = ''
              AND s.expires_at > ?
              AND u.status = 'active'
              AND u.account_status IN ('ACTIVE', 'RESET_REQUIRED')
              AND tm.status = 'active'
              AND t.status = 'active'
            LIMIT 1
            """,
            (str(token_hash), str(now)),
        ).fetchone()
        return dict(row) if row else None

    def touch_session(self, session_key: str) -> None:
        self.db.connection.execute(
            "UPDATE auth_sessions SET last_seen_at = ? WHERE session_key = ?",
            (self._utc_now(), str(session_key)),
        )
        self.db.connection.commit()

    def revoke_session(self, token_hash: str) -> bool:
        cursor = self.db.connection.execute(
            """
            UPDATE auth_sessions SET revoked_at = ?
            WHERE token_hash = ? AND revoked_at = ''
            """,
            (self._utc_now(), str(token_hash)),
        )
        self.db.connection.commit()
        return cursor.rowcount > 0

    def revoke_all_sessions_for_user(self, user_id: int, *, commit: bool = True) -> int:
        cursor = self.db.connection.execute(
            """
            UPDATE auth_sessions SET revoked_at = ?
            WHERE user_id = ? AND revoked_at = ''
            """,
            (self._utc_now(), int(user_id)),
        )
        if commit:
            self.db.connection.commit()
        return int(cursor.rowcount)

    # ------------------------------------------------------------------
    # Password reset requests, audit, and imports
    # ------------------------------------------------------------------

    def create_password_reset_request(self, requested_user_id: str) -> None:
        requested = str(requested_user_id or "").strip()
        user = self.get_user_by_login_id(requested)
        now = self._utc_now()
        self.db.connection.execute(
            """
            INSERT INTO password_reset_requests
            (user_id, requested_user_id, status, requested_at, resolved_at, resolved_by_user_id)
            VALUES (?, ?, 'pending', ?, '', NULL)
            """,
            (int(user["id"]) if user else None, requested, now),
        )
        if user:
            self.db.connection.execute(
                "UPDATE users SET forgot_password_requested_at = ?, updated_at = ? WHERE id = ?",
                (now, now, int(user["id"])),
            )
        self.db.connection.commit()

    def list_pending_password_reset_requests(
        self,
        *,
        country_location: str | None = None,
    ) -> list[dict[str, Any]]:
        params: list[Any] = []
        scope = ""
        if country_location is not None:
            scope = " AND LOWER(u.country_location) = LOWER(?)"
            params.append(str(country_location))
        rows = self.db.connection.execute(
            f"""
            SELECT pr.id, pr.requested_user_id, pr.requested_at, pr.status,
                   u.id AS database_user_id, u.display_name, u.email,
                   u.country_location, u.role_code
            FROM password_reset_requests pr
            LEFT JOIN users u ON u.id = pr.user_id
            WHERE pr.status = 'pending'{scope}
            ORDER BY pr.requested_at DESC
            """,
            tuple(params),
        ).fetchall()
        return [dict(row) for row in rows]

    def resolve_password_reset_requests(self, user_id: int, resolved_by_user_id: int) -> int:
        cursor = self.db.connection.execute(
            """
            UPDATE password_reset_requests
            SET status = 'resolved', resolved_at = ?, resolved_by_user_id = ?
            WHERE user_id = ? AND status = 'pending'
            """,
            (self._utc_now(), int(resolved_by_user_id), int(user_id)),
        )
        self.db.connection.commit()
        return int(cursor.rowcount)

    def record_import_job(
        self,
        *,
        uploaded_by_user_id: int,
        filename: str,
        total_rows: int,
        created_rows: int,
        skipped_rows: int,
        failed_rows: int,
        summary: dict[str, Any],
    ) -> int:
        now = self._utc_now()
        cursor = self.db.connection.execute(
            """
            INSERT INTO user_import_jobs
            (uploaded_by_user_id, filename, total_rows, created_rows,
             skipped_rows, failed_rows, status, summary_json, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, 'completed', ?, ?, ?)
            """,
            (
                int(uploaded_by_user_id),
                str(filename or ""),
                int(total_rows),
                int(created_rows),
                int(skipped_rows),
                int(failed_rows),
                json.dumps(summary, ensure_ascii=False),
                now,
                now,
            ),
        )
        self.db.connection.commit()
        return int(cursor.lastrowid)

    def audit_event(
        self,
        *,
        tenant_id: int | None,
        actor_user_id: int | None,
        action: str,
        target_type: str = "",
        target_id: str = "",
        details: dict[str, Any] | None = None,
        outcome: str = "success",
    ) -> int:
        cursor = self.db.connection.execute(
            """
            INSERT INTO audit_events
            (tenant_id, actor_user_id, action, target_type, target_id,
             details_json, outcome, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tenant_id,
                actor_user_id,
                str(action),
                str(target_type or ""),
                str(target_id or ""),
                json.dumps(details or {}, ensure_ascii=False),
                str(outcome or "success"),
                self._utc_now(),
            ),
        )
        self.db.connection.commit()
        return int(cursor.lastrowid)

    def list_audit_events(
        self,
        *,
        actor_user_ids: Iterable[int] | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        params: list[Any] = []
        where = ""
        ids = list(actor_user_ids or [])
        if ids:
            placeholders = ",".join("?" for _ in ids)
            where = f"WHERE actor_user_id IN ({placeholders})"
            params.extend(int(value) for value in ids)
        params.append(max(1, min(int(limit), 1000)))
        rows = self.db.connection.execute(
            f"""
            SELECT id, tenant_id, actor_user_id, action, target_type,
                   target_id, details_json, outcome, created_at
            FROM audit_events
            {where}
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()
        return [dict(row) for row in rows]

    def count_active_users(self) -> int:
        row = self.db.connection.execute(
            """
            SELECT COUNT(*) AS total FROM users
            WHERE status = 'active' AND account_status IN ('ACTIVE', 'RESET_REQUIRED')
            """
        ).fetchone()
        return int(row["total"] if row else 0)

    def close(self) -> None:
        if self._owns_database:
            self.db.close()

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")
