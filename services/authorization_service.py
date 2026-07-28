"""Role-based authorization policy for RecruitOS."""
from __future__ import annotations

from dataclasses import dataclass

from models.security_context import SecurityContext


SYSTEM_OWNER = "SYSTEM_OWNER"
GLOBAL_ADMIN = "GLOBAL_ADMIN"
TENANT_ADMIN = "TENANT_ADMIN"
USER = "USER"
READER = "READER"

ROLE_LABELS = {
    SYSTEM_OWNER: "System Owner",
    GLOBAL_ADMIN: "Global Admin",
    TENANT_ADMIN: "Tenant Admin",
    USER: "User",
    READER: "Reader",
}

PERMISSION_HOME = "HOME_VIEW"
PERMISSION_SCREEN = "SCREENING_RUN"
PERMISSION_RESULTS = "RESULTS_VIEW_OWN"
PERMISSION_CANDIDATES = "CANDIDATES_VIEW_OWN"
PERMISSION_USER_MANAGE_GLOBAL = "USER_MANAGE_GLOBAL"
PERMISSION_USER_MANAGE_TENANT = "USER_MANAGE_TENANT"
PERMISSION_ROLE_ASSIGN_GLOBAL = "ROLE_ASSIGN_GLOBAL"
PERMISSION_ROLE_ASSIGN_TENANT = "ROLE_ASSIGN_TENANT"
PERMISSION_ACCESS_MASTER = "USER_ACCESS_MASTER_EXPORT"
PERMISSION_SHARED_READ = "SHARED_RECORDS_READ"
PERMISSION_SYSTEM_POLICY = "SYSTEM_POLICY_MANAGE"
PERMISSION_CONFIGURATION_VIEW = "CONFIGURATION_VIEW"
PERMISSION_CONFIGURATION_MANAGE_GLOBAL = "CONFIGURATION_MANAGE_GLOBAL"
PERMISSION_CONFIGURATION_MANAGE_TENANT = "CONFIGURATION_MANAGE_TENANT"

_ROLE_PERMISSIONS = {
    SYSTEM_OWNER: {
        PERMISSION_HOME,
        PERMISSION_SCREEN,
        PERMISSION_RESULTS,
        PERMISSION_CANDIDATES,
        PERMISSION_USER_MANAGE_GLOBAL,
        PERMISSION_USER_MANAGE_TENANT,
        PERMISSION_ROLE_ASSIGN_GLOBAL,
        PERMISSION_ROLE_ASSIGN_TENANT,
        PERMISSION_ACCESS_MASTER,
        PERMISSION_SHARED_READ,
        PERMISSION_SYSTEM_POLICY,
        PERMISSION_CONFIGURATION_VIEW,
        PERMISSION_CONFIGURATION_MANAGE_GLOBAL,
        PERMISSION_CONFIGURATION_MANAGE_TENANT,
    },
    GLOBAL_ADMIN: {
        PERMISSION_HOME,
        PERMISSION_SCREEN,
        PERMISSION_RESULTS,
        PERMISSION_CANDIDATES,
        PERMISSION_USER_MANAGE_GLOBAL,
        PERMISSION_USER_MANAGE_TENANT,
        PERMISSION_ROLE_ASSIGN_TENANT,
        PERMISSION_ACCESS_MASTER,
        PERMISSION_SHARED_READ,
        PERMISSION_CONFIGURATION_VIEW,
        PERMISSION_CONFIGURATION_MANAGE_GLOBAL,
        PERMISSION_CONFIGURATION_MANAGE_TENANT,
    },
    TENANT_ADMIN: {
        PERMISSION_HOME,
        PERMISSION_SCREEN,
        PERMISSION_RESULTS,
        PERMISSION_CANDIDATES,
        PERMISSION_USER_MANAGE_TENANT,
        PERMISSION_ROLE_ASSIGN_TENANT,
        PERMISSION_ACCESS_MASTER,
        PERMISSION_SHARED_READ,
        PERMISSION_CONFIGURATION_VIEW,
        PERMISSION_CONFIGURATION_MANAGE_TENANT,
    },
    USER: {
        PERMISSION_HOME,
        PERMISSION_SCREEN,
        PERMISSION_RESULTS,
        PERMISSION_CANDIDATES,
        PERMISSION_CONFIGURATION_VIEW,
    },
    READER: {
        PERMISSION_HOME,
        PERMISSION_SHARED_READ,
    },
}

_PAGE_PERMISSION = {
    "Home": PERMISSION_HOME,
    "Resume Screening": PERMISSION_SCREEN,
    "Results": PERMISSION_RESULTS,
    "Candidate Database": PERMISSION_CANDIDATES,
    "Administration": PERMISSION_USER_MANAGE_TENANT,
    "Configuration": PERMISSION_CONFIGURATION_VIEW,
    "Shared Records": PERMISSION_SHARED_READ,
}


@dataclass(frozen=True, slots=True)
class RoleDecision:
    allowed: bool
    reason: str = ""


class AuthorizationService:
    """Evaluate RBAC independently from private-record ownership checks."""

    @staticmethod
    def normalize_role(role: str) -> str:
        value = str(role or "").strip().upper().replace(" ", "_")
        if value not in ROLE_LABELS:
            raise ValueError(f"Unsupported RecruitOS role: {role!r}")
        return value

    @classmethod
    def permissions_for_role(cls, role: str) -> frozenset[str]:
        normalized = cls.normalize_role(role)
        return frozenset(_ROLE_PERMISSIONS[normalized])

    @classmethod
    def has_permission(cls, context: SecurityContext, permission: str) -> bool:
        context.require_valid()
        return str(permission) in cls.permissions_for_role(context.role)

    @classmethod
    def require_permission(cls, context: SecurityContext, permission: str) -> None:
        if not cls.has_permission(context, permission):
            raise PermissionError(
                f"Role {ROLE_LABELS.get(context.role, context.role)} is not permitted "
                f"to perform this action."
            )

    @classmethod
    def pages_for_context(cls, context: SecurityContext) -> list[str]:
        context.require_valid()
        pages: list[str] = []
        for page, permission in _PAGE_PERMISSION.items():
            if cls.has_permission(context, permission):
                pages.append(page)
        return pages

    @classmethod
    def assignable_roles(cls, context: SecurityContext) -> list[str]:
        """Return roles the actor is allowed to provision or assign."""
        role = cls.normalize_role(context.role)
        if role == SYSTEM_OWNER:
            return [GLOBAL_ADMIN, TENANT_ADMIN, USER, READER]
        if role == GLOBAL_ADMIN:
            return [TENANT_ADMIN, USER, READER]
        if role == TENANT_ADMIN:
            return [USER, READER]
        return []

    @classmethod
    def can_manage_target(
        cls,
        context: SecurityContext,
        *,
        target_role: str,
        target_country_location: str,
    ) -> RoleDecision:
        actor_role = cls.normalize_role(context.role)
        target = cls.normalize_role(target_role)
        if target == SYSTEM_OWNER:
            return RoleDecision(False, "System Owner accounts cannot be managed here.")
        if actor_role == SYSTEM_OWNER:
            return RoleDecision(True)
        if actor_role == GLOBAL_ADMIN:
            if target == GLOBAL_ADMIN:
                return RoleDecision(False, "Only the System Owner can manage Global Admins.")
            return RoleDecision(True)
        if actor_role == TENANT_ADMIN:
            if target not in {USER, READER}:
                return RoleDecision(False, "Tenant Admins can manage User and Reader roles only.")
            if str(context.country_location or "").casefold() != str(
                target_country_location or ""
            ).casefold():
                return RoleDecision(
                    False,
                    "Tenant Admins can manage users only in their assigned country/location.",
                )
            return RoleDecision(True)
        return RoleDecision(False, "This role cannot manage users.")
