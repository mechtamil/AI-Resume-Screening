"""Deployment guard tests for the one-time System Owner bootstrap."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.auth_service import AuthService
from tests.security_test_utils import TEST_LOCATION, TEST_PASSWORD


class DeploymentSecurityTests(unittest.TestCase):
    def _bootstrap(self, path: Path, setup_key: str = ""):
        return AuthService.bootstrap_system_owner(
            user_id="OWNER-1",
            full_name="System Owner",
            email="owner@example.com",
            country_location=TEST_LOCATION,
            password=TEST_PASSWORD,
            setup_key=setup_key,
            database_path=path,
        )

    def test_shared_deployment_without_setup_key_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "security.db"
            with (
                patch("services.auth_service.INITIAL_OWNER_SETUP_ENABLED", False),
                patch("services.auth_service.INITIAL_SETUP_KEY", ""),
            ):
                with self.assertRaisesRegex(PermissionError, "securely disabled|disabled"):
                    self._bootstrap(path)

    def test_configured_setup_key_is_required_and_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "security.db"
            with (
                patch("services.auth_service.INITIAL_OWNER_SETUP_ENABLED", True),
                patch("services.auth_service.INITIAL_SETUP_KEY", "correct-key"),
            ):
                with self.assertRaisesRegex(PermissionError, "not valid"):
                    self._bootstrap(path, "wrong-key")
                created = self._bootstrap(path, "correct-key")
                self.assertEqual(created["employee_user_id"], "OWNER-1")

    def test_existing_owner_cannot_be_recreated_even_when_gate_is_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "security.db"
            with (
                patch("services.auth_service.INITIAL_OWNER_SETUP_ENABLED", True),
                patch("services.auth_service.INITIAL_SETUP_KEY", ""),
            ):
                self._bootstrap(path)
            with patch("services.auth_service.INITIAL_OWNER_SETUP_ENABLED", False):
                with self.assertRaisesRegex(PermissionError, "already been configured"):
                    self._bootstrap(path)


if __name__ == "__main__":
    unittest.main()
