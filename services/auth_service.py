"""Admin-provisioned authentication and credential lifecycle for RecruitOS."""
from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from config.settings import (
    AUTH_LOCKOUT_MINUTES,
    AUTH_MAX_FAILED_LOGINS,
    AUTH_SESSION_HOURS,
    FORGOT_PASSWORD_GENERIC_MESSAGE,
    INITIAL_OWNER_SETUP_ENABLED,
    INITIAL_SETUP_KEY,
)
from database.user_repository import UserRepository
from models.security_context import SecurityContext
from services.password_service import PasswordService


class AuthService:
    """Authenticate employee IDs and issue opaque server-validated sessions."""

    EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

    @classmethod
    def owner_setup_required(
        cls,
        database_path: str | Path | None = None,
    ) -> bool:
        repository = UserRepository(database_path)
        try:
            return not repository.has_system_owner()
        finally:
            repository.close()

    @classmethod
    def bootstrap_system_owner(
        cls,
        *,
        user_id: str,
        full_name: str,
        email: str,
        country_location: str,
        password: str,
        setup_key: str = "",
        database_path: str | Path | None = None,
    ) -> dict[str, int | str | bool]:
        """Create the one and only initial System Owner through the UI.

        Shared/public deployments fail closed unless a deployment setup key is
        configured. Existing owners are detected before evaluating the setup gate
        so a second bootstrap always returns the correct lifecycle error.
        """
        repository = UserRepository(database_path)
        try:
            if repository.has_system_owner():
                raise PermissionError(
                    "The initial System Owner has already been configured."
                )
        finally:
            repository.close()

        if not INITIAL_OWNER_SETUP_ENABLED:
            raise PermissionError(
                "Initial System Owner setup is disabled because no deployment "
                "setup key is configured."
            )

        if INITIAL_SETUP_KEY and not secrets.compare_digest(
            str(setup_key or ""), INITIAL_SETUP_KEY
        ):
            raise PermissionError("The initial setup key is not valid.")

        login_id = cls.normalize_user_id(user_id)
        display_name = str(full_name or "").strip()
        email_value = cls.normalize_email(email)
        location = str(country_location or "").strip()
        cls._validate_identity(login_id, display_name, email_value, location)
        password_hash, salt, iterations = PasswordService.hash_password(password)

        repository = UserRepository(database_path)
        try:
            created = repository.create_system_owner(
                employee_user_id=login_id,
                display_name=display_name,
                email=email_value,
                country_location=location,
                password_hash=password_hash,
                password_salt=salt,
                password_iterations=iterations,
            )
            repository.audit_event(
                tenant_id=int(created["tenant_id"]),
                actor_user_id=int(created["user_id"]),
                action="SYSTEM_OWNER_BOOTSTRAPPED",
                target_type="user",
                target_id=str(created["user_id"]),
                details={"employee_user_id": login_id},
            )
            return created
        finally:
            repository.close()

    @classmethod
    def authenticate(
        cls,
        *,
        user_id: str,
        password: str,
        database_path: str | Path | None = None,
    ) -> tuple[SecurityContext, str]:
        login_id = cls.normalize_user_id(user_id)
        repository = UserRepository(database_path)
        try:
            user = repository.get_user_by_login_id(login_id)
            if not user:
                raise ValueError("Invalid User ID or password.")

            cls._assert_account_available(user)
            verified = PasswordService.verify_password(
                password,
                str(user.get("password_hash") or ""),
                str(user.get("password_salt") or ""),
                int(user.get("password_iterations") or 0),
            )
            if not verified:
                cls._record_failure(repository, user)
                repository.audit_event(
                    tenant_id=int(user["tenant_id"]),
                    actor_user_id=int(user["id"]),
                    action="LOGIN_FAILED",
                    target_type="user",
                    target_id=str(user["id"]),
                    outcome="failure",
                )
                raise ValueError("Invalid User ID or password.")

            repository.record_successful_login(int(user["id"]))
            context, raw_token = cls._issue_session(repository, user)
            repository.audit_event(
                tenant_id=context.tenant_id,
                actor_user_id=context.user_id,
                action="LOGIN_SUCCEEDED",
                target_type="user",
                target_id=str(context.user_id),
            )
            return context, raw_token
        finally:
            repository.close()

    @classmethod
    def resolve_session(
        cls,
        raw_token: str,
        database_path: str | Path | None = None,
    ) -> SecurityContext | None:
        token = str(raw_token or "").strip()
        if not token:
            return None
        repository = UserRepository(database_path)
        try:
            now = cls._utc_now()
            session = repository.get_active_session(cls._token_hash(token), now=now)
            if not session:
                return None
            repository.touch_session(str(session["session_key"]))
            context = cls._context_from_record(session)
            context.require_valid()
            return context
        finally:
            repository.close()

    @classmethod
    def complete_password_change(
        cls,
        *,
        raw_token: str,
        current_password: str,
        new_password: str,
        database_path: str | Path | None = None,
    ) -> tuple[SecurityContext, str]:
        """Change a password, revoke old sessions, and issue a fresh session."""
        token = str(raw_token or "").strip()
        context = cls.resolve_session(token, database_path)
        if context is None:
            raise PermissionError("Your sign-in session has expired.")

        PasswordService.validate_permanent_password(new_password)
        repository = UserRepository(database_path)
        try:
            user = repository.get_user_by_id(context.user_id)
            if not user or not PasswordService.verify_password(
                current_password,
                str(user.get("password_hash") or ""),
                str(user.get("password_salt") or ""),
                int(user.get("password_iterations") or 0),
            ):
                raise ValueError("The current password is not correct.")
            if PasswordService.verify_password(
                new_password,
                str(user.get("password_hash") or ""),
                str(user.get("password_salt") or ""),
                int(user.get("password_iterations") or 0),
            ):
                raise ValueError("The new password must be different from the current password.")

            password_hash, salt, iterations = PasswordService.hash_password(new_password)
            repository.update_password(
                context.user_id,
                password_hash=password_hash,
                password_salt=salt,
                password_iterations=iterations,
                account_status="ACTIVE",
                must_change_password=False,
                temporary_password_expires_at="",
                updated_by_user_id=context.user_id,
            )
            repository.revoke_all_sessions_for_user(context.user_id)
            refreshed = repository.get_user_by_id(context.user_id)
            if not refreshed:
                raise RuntimeError("The updated account could not be reloaded.")
            new_context, new_token = cls._issue_session(repository, refreshed)
            repository.audit_event(
                tenant_id=new_context.tenant_id,
                actor_user_id=new_context.user_id,
                action="PASSWORD_CHANGED",
                target_type="user",
                target_id=str(new_context.user_id),
            )
            return new_context, new_token
        finally:
            repository.close()

    @classmethod
    def request_password_reset(
        cls,
        user_id: str,
        database_path: str | Path | None = None,
    ) -> str:
        """Record an administrator-assisted request without exposing account existence."""
        repository = UserRepository(database_path)
        try:
            repository.create_password_reset_request(cls.normalize_user_id(user_id))
        finally:
            repository.close()
        return FORGOT_PASSWORD_GENERIC_MESSAGE

    @classmethod
    def logout(
        cls,
        raw_token: str,
        database_path: str | Path | None = None,
    ) -> bool:
        token = str(raw_token or "").strip()
        if not token:
            return False
        repository = UserRepository(database_path)
        try:
            session = repository.get_active_session(cls._token_hash(token), now=cls._utc_now())
            revoked = repository.revoke_session(cls._token_hash(token))
            if revoked and session:
                repository.audit_event(
                    tenant_id=int(session["tenant_id"]),
                    actor_user_id=int(session["user_id"]),
                    action="LOGOUT",
                    target_type="user",
                    target_id=str(session["user_id"]),
                )
            return revoked
        finally:
            repository.close()

    @staticmethod
    def normalize_user_id(user_id: str) -> str:
        return str(user_id or "").strip()

    @staticmethod
    def normalize_email(email: str) -> str:
        return str(email or "").strip().casefold()

    @classmethod
    def _validate_identity(
        cls,
        login_id: str,
        display_name: str,
        email: str,
        country_location: str,
    ) -> None:
        if len(login_id) < 1 or len(login_id) > 50:
            raise ValueError("User ID must contain between 1 and 50 characters.")
        if any(character.isspace() for character in login_id):
            raise ValueError("User ID cannot contain spaces.")
        if len(display_name) < 2 or len(display_name) > 120:
            raise ValueError("Full name must contain between 2 and 120 characters.")
        if not cls.EMAIL_PATTERN.fullmatch(email):
            raise ValueError("Enter a valid email address.")
        if not country_location:
            raise ValueError("Country or Location is required for the user profile.")

    @classmethod
    def _assert_account_available(cls, user: dict[str, Any]) -> None:
        if str(user.get("status") or "") != "active":
            raise PermissionError("This RecruitOS account is not active.")
        if str(user.get("membership_status") or "") != "active":
            raise PermissionError("This RecruitOS workspace membership is not active.")
        if str(user.get("tenant_status") or "") != "active":
            raise PermissionError("This RecruitOS workspace is not active.")

        account_status = str(user.get("account_status") or "").upper()
        if account_status not in {"ACTIVE", "RESET_REQUIRED"}:
            raise PermissionError("This RecruitOS account is not available for sign in.")

        now = datetime.now(timezone.utc)
        locked_until = str(user.get("locked_until") or "")
        if locked_until:
            try:
                lock_time = datetime.fromisoformat(locked_until)
            except ValueError:
                lock_time = None
            if lock_time and lock_time > now:
                raise PermissionError("Too many failed logins. Try again later.")

        valid_from = cls._parse_datetime(str(user.get("valid_from") or ""))
        valid_until = cls._parse_datetime(str(user.get("valid_until") or ""), end_of_day=True)
        if valid_from and now < valid_from:
            raise PermissionError("This RecruitOS account is not active yet.")
        if valid_until and now > valid_until:
            raise PermissionError("This RecruitOS account has expired.")

        if bool(user.get("must_change_password")):
            expiry = cls._parse_datetime(str(user.get("temporary_password_expires_at") or ""))
            if expiry and now > expiry:
                raise PermissionError(
                    "The temporary password has expired. Contact your RecruitOS administrator."
                )

    @classmethod
    def _issue_session(
        cls,
        repository: UserRepository,
        user: dict[str, Any],
    ) -> tuple[SecurityContext, str]:
        raw_token = secrets.token_urlsafe(48)
        expires_at = (
            datetime.now(timezone.utc) + timedelta(hours=AUTH_SESSION_HOURS)
        ).isoformat(timespec="seconds")
        session_key = repository.create_auth_session(
            user_id=int(user["id"]),
            tenant_id=int(user["tenant_id"]),
            token_hash=cls._token_hash(raw_token),
            expires_at=expires_at,
        )
        record = dict(user)
        record.update({"session_key": session_key, "expires_at": expires_at})
        return cls._context_from_record(record), raw_token

    @staticmethod
    def _context_from_record(record: dict[str, Any]) -> SecurityContext:
        return SecurityContext(
            user_id=int(record["user_id"] if "user_id" in record else record["id"]),
            tenant_id=int(record["tenant_id"]),
            login_id=str(record.get("employee_user_id") or ""),
            email=str(record.get("email") or ""),
            display_name=str(record.get("display_name") or record.get("employee_user_id") or ""),
            role=str(record.get("role_code") or record.get("membership_role") or "USER"),
            country_location=str(record.get("country_location") or ""),
            account_status=str(record.get("account_status") or "ACTIVE"),
            must_change_password=bool(record.get("must_change_password")),
            session_key=str(record.get("session_key") or ""),
            expires_at=str(record.get("expires_at") or ""),
        )

    @staticmethod
    def _record_failure(repository: UserRepository, user: dict[str, Any]) -> None:
        failures = int(user.get("failed_login_count") or 0) + 1
        locked_until = ""
        if failures >= AUTH_MAX_FAILED_LOGINS:
            locked_until = (
                datetime.now(timezone.utc) + timedelta(minutes=AUTH_LOCKOUT_MINUTES)
            ).isoformat(timespec="seconds")
        repository.record_failed_login(
            int(user["id"]),
            failed_count=failures,
            locked_until=locked_until,
        )

    @staticmethod
    def _token_hash(raw_token: str) -> str:
        return hashlib.sha256(str(raw_token).encode("utf-8")).hexdigest()

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    @staticmethod
    def _parse_datetime(value: str, *, end_of_day: bool = False) -> datetime | None:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            try:
                parsed = datetime.fromisoformat(f"{text}T{'23:59:59' if end_of_day else '00:00:00'}")
            except ValueError:
                return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
