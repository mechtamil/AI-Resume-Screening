"""Authenticated RecruitOS identity and authorization context."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SecurityContext:
    """Identity and authorization scope used by every protected operation."""

    user_id: int
    tenant_id: int
    email: str
    display_name: str
    role: str = "USER"
    login_id: str = ""
    country_location: str = ""
    account_status: str = "ACTIVE"
    must_change_password: bool = False
    session_key: str = ""
    expires_at: str = ""

    def require_valid(self) -> None:
        """Reject incomplete or forged-looking security contexts."""
        if int(self.user_id or 0) <= 0:
            raise PermissionError("Authentication is required.")
        if int(self.tenant_id or 0) <= 0:
            raise PermissionError("A private workspace is required.")
        if not str(self.login_id or "").strip():
            raise PermissionError("Authenticated User ID is missing.")
        if not str(self.role or "").strip():
            raise PermissionError("Authenticated role is missing.")
        if str(self.account_status or "").upper() not in {
            "ACTIVE",
            "RESET_REQUIRED",
        }:
            raise PermissionError("This RecruitOS account is not available.")

    def summary(self) -> dict[str, str | int | bool]:
        return {
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "login_id": self.login_id,
            "email": self.email,
            "display_name": self.display_name,
            "role": self.role,
            "country_location": self.country_location,
            "account_status": self.account_status,
            "must_change_password": self.must_change_password,
        }
