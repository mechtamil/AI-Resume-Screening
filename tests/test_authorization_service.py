"""Role-based access-control policy tests."""
from __future__ import annotations

import unittest

from models.security_context import SecurityContext
from services.authorization_service import (
    GLOBAL_ADMIN,
    READER,
    SYSTEM_OWNER,
    TENANT_ADMIN,
    USER,
    AuthorizationService,
)


def context(role: str, location: str = "India - Chennai") -> SecurityContext:
    return SecurityContext(
        user_id=1,
        tenant_id=1,
        login_id="6276",
        email="user@example.com",
        display_name="Test User",
        role=role,
        country_location=location,
    )


class AuthorizationServiceTests(unittest.TestCase):
    def test_page_access_matches_approved_roles(self):
        self.assertIn("Administration", AuthorizationService.pages_for_context(context(SYSTEM_OWNER)))
        self.assertIn("Administration", AuthorizationService.pages_for_context(context(GLOBAL_ADMIN)))
        self.assertIn("Administration", AuthorizationService.pages_for_context(context(TENANT_ADMIN)))
        self.assertNotIn("Administration", AuthorizationService.pages_for_context(context(USER)))
        self.assertEqual(
            AuthorizationService.pages_for_context(context(READER)),
            ["Home", "Shared Records"],
        )

    def test_assignable_roles_follow_privilege_boundaries(self):
        self.assertEqual(
            AuthorizationService.assignable_roles(context(SYSTEM_OWNER)),
            [GLOBAL_ADMIN, TENANT_ADMIN, USER, READER],
        )
        self.assertEqual(
            AuthorizationService.assignable_roles(context(GLOBAL_ADMIN)),
            [TENANT_ADMIN, USER, READER],
        )
        self.assertEqual(
            AuthorizationService.assignable_roles(context(TENANT_ADMIN)),
            [USER, READER],
        )
        self.assertEqual(AuthorizationService.assignable_roles(context(USER)), [])

    def test_tenant_admin_is_location_scoped(self):
        actor = context(TENANT_ADMIN, "India - Chennai")
        allowed = AuthorizationService.can_manage_target(
            actor,
            target_role=USER,
            target_country_location="India - Chennai",
        )
        blocked_location = AuthorizationService.can_manage_target(
            actor,
            target_role=USER,
            target_country_location="France - Paris",
        )
        blocked_role = AuthorizationService.can_manage_target(
            actor,
            target_role=GLOBAL_ADMIN,
            target_country_location="India - Chennai",
        )
        self.assertTrue(allowed.allowed)
        self.assertFalse(blocked_location.allowed)
        self.assertFalse(blocked_role.allowed)

    def test_system_owner_account_cannot_be_managed_from_user_admin(self):
        decision = AuthorizationService.can_manage_target(
            context(SYSTEM_OWNER),
            target_role=SYSTEM_OWNER,
            target_country_location="India - Chennai",
        )
        self.assertFalse(decision.allowed)


if __name__ == "__main__":
    unittest.main()
