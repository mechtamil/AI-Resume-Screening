"""Tenant configuration versioning, RBAC, and integrity tests."""
from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from openpyxl import load_workbook

from config.paths import CONFIGURATION_WORKBOOK
from services.tenant_configuration_service import TenantConfigurationService
from tests.security_test_utils import create_context, create_owner_context


def _custom_workbook(root: Path, name: str, skill: str) -> Path:
    path = root / name
    shutil.copy2(CONFIGURATION_WORKBOOK, path)
    workbook = load_workbook(path)
    sheet = workbook["Skills"]
    headers = [cell.value for cell in sheet[1]]
    values = {
        "Skill": skill,
        "Category": "Custom",
        "Sub Category": "Tenant",
        "Synonyms": f"{skill} Alias",
        "Active": "Yes",
    }
    sheet.append([values.get(header, "") for header in headers])
    workbook.save(path)
    return path


class TenantConfigurationServiceTests(unittest.TestCase):
    def test_owner_can_publish_activate_download_and_revert_user_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database_path = root / "configuration.db"
            owner = create_owner_context(database_path)
            user = create_context(database_path, "config.user@example.com", "Config User")
            service = TenantConfigurationService(
                database_path,
                private_root=root / "private-configurations",
                system_default_path=CONFIGURATION_WORKBOOK,
            )
            workbook_path = _custom_workbook(root, "custom.xlsx", "Tenant Custom Skill")

            created = service.upload_version(
                owner,
                target_user_id=user.user_id,
                file_name="custom.xlsx",
                content=workbook_path.read_bytes(),
                activate=True,
            )
            self.assertEqual(created["status"], "ACTIVE")
            self.assertEqual(created["version_number"], 1)

            active = service.resolve_active(user)
            self.assertEqual(active.source, "tenant_version")
            self.assertEqual(active.version_id, created["id"])
            self.assertEqual(active.sha256, created["file_sha256"])

            versions = service.list_versions(user)
            self.assertEqual(len(versions), 1)
            name, content = service.download_version(
                user,
                target_user_id=user.user_id,
            )
            self.assertIn("v1", name)
            self.assertEqual(content, active.workbook_path.read_bytes())

            default_selection = service.use_system_default(
                owner,
                target_user_id=user.user_id,
            )
            self.assertEqual(default_selection.source, "system_default")
            self.assertEqual(service.resolve_active(user).source, "system_default")

    def test_standard_user_cannot_publish_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database_path = root / "configuration.db"
            user = create_context(database_path, "plain.user@example.com", "Plain User")
            workbook_path = _custom_workbook(root, "custom.xlsx", "Private Skill")
            service = TenantConfigurationService(
                database_path,
                private_root=root / "private-configurations",
                system_default_path=CONFIGURATION_WORKBOOK,
            )

            with self.assertRaisesRegex(PermissionError, "cannot manage"):
                service.upload_version(
                    user,
                    target_user_id=user.user_id,
                    file_name="custom.xlsx",
                    content=workbook_path.read_bytes(),
                    activate=True,
                )

    def test_duplicate_upload_and_file_tampering_are_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database_path = root / "configuration.db"
            owner = create_owner_context(database_path)
            user = create_context(database_path, "integrity.user@example.com", "Integrity User")
            workbook_path = _custom_workbook(root, "custom.xlsx", "Integrity Skill")
            content = workbook_path.read_bytes()
            service = TenantConfigurationService(
                database_path,
                private_root=root / "private-configurations",
                system_default_path=CONFIGURATION_WORKBOOK,
            )

            service.upload_version(
                owner,
                target_user_id=user.user_id,
                file_name="custom.xlsx",
                content=content,
                activate=True,
            )
            with self.assertRaisesRegex(ValueError, "already exists"):
                service.upload_version(
                    owner,
                    target_user_id=user.user_id,
                    file_name="duplicate.xlsx",
                    content=content,
                )

            active = service.resolve_active(user)
            os.chmod(active.workbook_path, 0o644)
            with active.workbook_path.open("ab") as handle:
                handle.write(b"tampered")
            with self.assertRaisesRegex(ValueError, "integrity check"):
                service.resolve_active(user)


if __name__ == "__main__":
    unittest.main()
