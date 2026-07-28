"""Authentication and credential-lifecycle tests for RecruitOS."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from database.user_repository import UserRepository
from services.auth_service import AuthService
from services.authorization_service import SYSTEM_OWNER, USER
from services.user_management_service import UserManagementService
from tests.security_test_utils import (
    TEST_LOCATION,
    TEST_OWNER_USER_ID,
    TEST_PASSWORD,
    TEST_TEMPORARY_PASSWORD,
    create_owner_context,
)


class AuthServiceTests(unittest.TestCase):
    def test_owner_bootstrap_provision_login_reset_resolve_and_logout(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "auth.db"
            owner = create_owner_context(path)
            self.assertEqual(owner.role, SYSTEM_OWNER)
            self.assertFalse(owner.must_change_password)

            created = UserManagementService.create_user(
                owner,
                employee_user_id="6276",
                full_name="Tamilvanan Arumugam",
                email="tamilvanan@example.com",
                role=USER,
                country_location=TEST_LOCATION,
                temporary_password=TEST_TEMPORARY_PASSWORD,
                database_path=path,
            )
            self.assertEqual(created["employee_user_id"], "6276")
            self.assertTrue(created["must_change_password"])
            self.assertEqual(created["account_status"], "RESET_REQUIRED")

            temporary_context, temporary_token = AuthService.authenticate(
                user_id="6276",
                password=TEST_TEMPORARY_PASSWORD,
                database_path=path,
            )
            self.assertTrue(temporary_context.must_change_password)
            self.assertEqual(temporary_context.role, USER)
            self.assertEqual(temporary_context.login_id, "6276")

            resolved = AuthService.resolve_session(temporary_token, path)
            self.assertIsNotNone(resolved)
            self.assertEqual(resolved.user_id, temporary_context.user_id)

            active_context, active_token = AuthService.complete_password_change(
                raw_token=temporary_token,
                current_password=TEST_TEMPORARY_PASSWORD,
                new_password=TEST_PASSWORD,
                database_path=path,
            )
            self.assertFalse(active_context.must_change_password)
            self.assertEqual(active_context.account_status, "ACTIVE")
            self.assertIsNone(AuthService.resolve_session(temporary_token, path))
            self.assertIsNotNone(AuthService.resolve_session(active_token, path))

            self.assertTrue(AuthService.logout(active_token, path))
            self.assertIsNone(AuthService.resolve_session(active_token, path))

    def test_public_self_registration_api_is_removed(self):
        self.assertFalse(hasattr(AuthService, "register_user"))

    def test_duplicate_user_id_is_rejected_case_insensitively(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "auth.db"
            owner = create_owner_context(path)
            UserManagementService.create_user(
                owner,
                employee_user_id="IN-6276",
                full_name="First User",
                email="first@example.com",
                role=USER,
                country_location=TEST_LOCATION,
                temporary_password=TEST_TEMPORARY_PASSWORD,
                database_path=path,
            )
            with self.assertRaisesRegex(ValueError, "User ID already exists"):
                UserManagementService.create_user(
                    owner,
                    employee_user_id="in-6276",
                    full_name="Second User",
                    email="second@example.com",
                    role=USER,
                    country_location=TEST_LOCATION,
                    temporary_password=TEST_TEMPORARY_PASSWORD,
                    database_path=path,
                )

    def test_wrong_password_uses_generic_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "auth.db"
            owner = create_owner_context(path)
            with self.assertRaisesRegex(ValueError, "Invalid User ID or password"):
                AuthService.authenticate(
                    user_id=TEST_OWNER_USER_ID,
                    password="This Password Is Wrong!",
                    database_path=path,
                )

    def test_short_temporary_password_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "auth.db"
            owner = create_owner_context(path)
            with self.assertRaisesRegex(ValueError, "at least 6"):
                UserManagementService.create_user(
                    owner,
                    employee_user_id="SHORT1",
                    full_name="Short Password",
                    email="short@example.com",
                    role=USER,
                    country_location=TEST_LOCATION,
                    temporary_password="12345",
                    database_path=path,
                )

    def test_forgot_password_response_does_not_disclose_account_existence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "auth.db"
            create_owner_context(path)
            known = AuthService.request_password_reset(TEST_OWNER_USER_ID, path)
            unknown = AuthService.request_password_reset("NOT-A-USER", path)
            self.assertEqual(known, unknown)

            repository = UserRepository(path)
            try:
                requests = repository.list_pending_password_reset_requests()
                self.assertEqual(len(requests), 2)
            finally:
                repository.close()

    def test_second_system_owner_bootstrap_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "auth.db"
            create_owner_context(path)
            with self.assertRaisesRegex(PermissionError, "already been configured"):
                AuthService.bootstrap_system_owner(
                    user_id="OTHER-OWNER",
                    full_name="Other Owner",
                    email="other.owner@example.com",
                    country_location=TEST_LOCATION,
                    password=TEST_PASSWORD,
                    database_path=path,
                )


if __name__ == "__main__":
    unittest.main()
