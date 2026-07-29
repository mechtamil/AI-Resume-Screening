"""Explicit project sharing and read-only review orchestration."""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any

from database.database import Database
from database.sharing_repository import SharingRepository
from database.user_repository import UserRepository
from models.security_context import SecurityContext
from services.authorization_service import (
    GLOBAL_ADMIN,
    SYSTEM_OWNER,
    PERMISSION_SHARED_MANAGE_OWN,
    PERMISSION_SHARED_READ,
    AuthorizationService,
)
from services.persistence_service import PersistenceService


class SharingService:
    """Expose explicit sharing without changing owner-scoped repositories."""

    ACCESS_READER = "READER"
    ACCESS_REVIEWER = "REVIEWER"
    REVIEW_ASSIGNED = "ASSIGNED"
    REVIEW_IN_REVIEW = "IN_REVIEW"
    REVIEW_COMPLETED = "COMPLETED"

    @classmethod
    def list_shareable_users(
        cls,
        context: SecurityContext,
        database_path: str | Path | None = None,
    ) -> list[dict[str, Any]]:
        """Return active recipients allowed by the actor's sharing scope."""
        AuthorizationService.require_permission(context, PERMISSION_SHARED_MANAGE_OWN)
        repository = UserRepository(database_path)
        try:
            users = repository.list_users(include_disabled=False)
        finally:
            repository.close()

        unrestricted = context.role in {SYSTEM_OWNER, GLOBAL_ADMIN}
        actor_location = str(context.country_location or "").strip().casefold()
        allowed: list[dict[str, Any]] = []
        for item in users:
            if int(item.get("id") or 0) == int(context.user_id):
                continue
            if str(item.get("account_status") or "").upper() not in {
                "ACTIVE",
                "RESET_REQUIRED",
            }:
                continue
            target_location = str(item.get("country_location") or "").strip().casefold()
            if not unrestricted and actor_location != target_location:
                continue
            allowed.append(item)
        return allowed

    @classmethod
    def grant_project_share(
        cls,
        context: SecurityContext,
        *,
        project_id: int,
        grantee_user_id: int,
        access_role: str,
        expires_at: str | date | datetime | None = None,
        note: str = "",
        database_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """Share one owned project with one explicitly selected recipient."""
        AuthorizationService.require_permission(context, PERMISSION_SHARED_MANAGE_OWN)
        normalized_expiry = cls._normalize_expiry(expires_at)
        cls._require_shareable_recipient(
            context,
            int(grantee_user_id),
            database_path,
        )
        repository = SharingRepository(context, database_path)
        try:
            return repository.grant_project_share(
                project_id=int(project_id),
                grantee_user_id=int(grantee_user_id),
                access_role=str(access_role),
                expires_at=normalized_expiry,
                note=str(note or "").strip()[:500],
            )
        finally:
            repository.close()

    @staticmethod
    def revoke_share(
        context: SecurityContext,
        share_id: int,
        database_path: str | Path | None = None,
    ) -> bool:
        AuthorizationService.require_permission(context, PERMISSION_SHARED_MANAGE_OWN)
        repository = SharingRepository(context, database_path)
        try:
            return repository.revoke_share(int(share_id))
        finally:
            repository.close()

    @staticmethod
    def list_owned_shares(
        context: SecurityContext,
        *,
        project_id: int | None = None,
        database_path: str | Path | None = None,
    ) -> list[dict[str, Any]]:
        AuthorizationService.require_permission(context, PERMISSION_SHARED_MANAGE_OWN)
        repository = SharingRepository(context, database_path)
        try:
            return repository.list_owned_shares(project_id=project_id)
        finally:
            repository.close()

    @staticmethod
    def list_received_shares(
        context: SecurityContext,
        database_path: str | Path | None = None,
    ) -> list[dict[str, Any]]:
        AuthorizationService.require_permission(context, PERMISSION_SHARED_READ)
        repository = SharingRepository(context, database_path)
        try:
            return repository.list_received_shares()
        finally:
            repository.close()

    @staticmethod
    def list_shared_sessions(
        context: SecurityContext,
        share_id: int,
        database_path: str | Path | None = None,
    ) -> list[dict[str, Any]]:
        AuthorizationService.require_permission(context, PERMISSION_SHARED_READ)
        repository = SharingRepository(context, database_path)
        try:
            return repository.list_received_sessions(int(share_id))
        finally:
            repository.close()

    @classmethod
    def load_shared_session(
        cls,
        context: SecurityContext,
        *,
        share_id: int,
        session_id: int,
        database_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """Load evidence only after a current active share authorizes the session."""
        AuthorizationService.require_permission(context, PERMISSION_SHARED_READ)
        database = Database(database_path)
        database.create_tables()
        shares = SharingRepository(context, database)
        users = UserRepository(database)
        try:
            share = shares.get_received_share(int(share_id))
            if not share:
                raise PermissionError("The shared project is not available.")

            allowed_session_ids = {
                int(item["id"])
                for item in shares.list_received_sessions(int(share_id))
            }
            if int(session_id) not in allowed_session_ids:
                raise PermissionError("The selected session is outside this share.")

            owner = users.get_user_by_id(int(share["owner_user_id"]))
            if not owner:
                raise LookupError("The shared project owner is not available.")
            if int(owner.get("tenant_id") or 0) != int(share["owner_tenant_id"]):
                raise PermissionError("The sharing ownership boundary is invalid.")

            owner_context = SecurityContext(
                user_id=int(owner["id"]),
                tenant_id=int(share["owner_tenant_id"]),
                login_id=str(owner.get("employee_user_id") or "OWNER"),
                email=str(owner.get("email") or ""),
                display_name=str(owner.get("display_name") or "Project owner"),
                role=str(owner.get("role_code") or "USER"),
                country_location=str(owner.get("country_location") or ""),
                account_status=str(owner.get("account_status") or "ACTIVE"),
            )
        finally:
            shares.close()
            # shares owns no database here; UserRepository also receives the same DB.
            users.close()
            database.close()

        result = PersistenceService.load_session(
            owner_context,
            int(session_id),
            database_path,
        )
        for candidate in list(result.get("candidates") or []):
            if hasattr(candidate, "raw_text"):
                candidate.raw_text = ""
        result["storage"] = {}
        result["persistence"] = {
            "shared_read_only": True,
            "share_id": int(share_id),
            "session_id": int(session_id),
        }
        result["sharing"] = {
            "share_id": int(share_id),
            "access_role": str(share.get("access_role") or "READER"),
            "owner_name": str(share.get("owner_name") or ""),
            "expires_at": str(share.get("expires_at") or ""),
            "review_status": str(share.get("review_status") or "NOT_REQUIRED"),
            "read_only": True,
        }
        return result

    @staticmethod
    def update_review(
        context: SecurityContext,
        *,
        share_id: int,
        review_status: str,
        review_note: str = "",
        database_path: str | Path | None = None,
    ) -> dict[str, Any]:
        AuthorizationService.require_permission(context, PERMISSION_SHARED_READ)
        repository = SharingRepository(context, database_path)
        try:
            return repository.update_review(
                int(share_id),
                review_status=str(review_status),
                review_note=str(review_note or "").strip()[:2000],
            )
        finally:
            repository.close()

    @staticmethod
    def list_share_audit(
        context: SecurityContext,
        share_id: int,
        database_path: str | Path | None = None,
    ) -> list[dict[str, Any]]:
        repository = SharingRepository(context, database_path)
        try:
            return repository.list_share_audit(int(share_id))
        finally:
            repository.close()

    @classmethod
    def _require_shareable_recipient(
        cls,
        context: SecurityContext,
        grantee_user_id: int,
        database_path: str | Path | None,
    ) -> None:
        if int(grantee_user_id) == int(context.user_id):
            raise ValueError("A project cannot be shared with its owner.")
        repository = UserRepository(database_path)
        try:
            target = repository.get_user_by_id(int(grantee_user_id))
        finally:
            repository.close()
        if not target or str(target.get("status") or "") != "active":
            raise LookupError("The selected recipient is not available.")
        if str(target.get("account_status") or "").upper() not in {
            "ACTIVE",
            "RESET_REQUIRED",
        }:
            raise LookupError("The selected recipient is not active.")

        if context.role not in {SYSTEM_OWNER, GLOBAL_ADMIN}:
            actor_location = str(context.country_location or "").strip().casefold()
            target_location = str(target.get("country_location") or "").strip().casefold()
            if actor_location != target_location:
                raise PermissionError(
                    "Projects can be shared only with recipients in your assigned country/location."
                )

    @staticmethod
    def _normalize_expiry(value: str | date | datetime | None) -> str:
        if value is None or str(value).strip() == "":
            return ""
        if isinstance(value, datetime):
            expiry = value
        elif isinstance(value, date):
            expiry = datetime.combine(value, time(23, 59, 59), tzinfo=timezone.utc)
        else:
            raw = str(value).strip()
            try:
                expiry = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                try:
                    expiry_date = date.fromisoformat(raw)
                except ValueError as exc:
                    raise ValueError("Share expiry must be an ISO date or datetime.") from exc
                expiry = datetime.combine(
                    expiry_date,
                    time(23, 59, 59),
                    tzinfo=timezone.utc,
                )
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        expiry = expiry.astimezone(timezone.utc)
        if expiry <= datetime.now(timezone.utc):
            raise ValueError("Share expiry must be in the future.")
        return expiry.isoformat(timespec="seconds")
