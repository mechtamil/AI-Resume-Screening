"""Tests for private Excel export persistence."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from JD.jd_model import JobDescription
from models.security_context import SecurityContext
from services.secure_export_service import SecureExportService
from services.secure_storage_service import SecureStorageService


class FakeReportBuilder:
    @staticmethod
    def default_filename(job_title: str) -> str:
        return f"{job_title or 'RecruitOS'}_Report.xlsx"

    @staticmethod
    def build_report(analysis_result: dict) -> bytes:
        return b"private-excel-content"


class SecureExportServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.storage = SecureStorageService(
            uploads_root=root / "uploads",
            temp_root=root / "temp",
            output_root=root / "output",
        )
        self.user_a = self._context(11, "A-11")
        self.user_b = self._context(12, "B-12")
        self.service = SecureExportService(self.storage, FakeReportBuilder)

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def _context(user_id: int, login_id: str) -> SecurityContext:
        return SecurityContext(
            user_id=user_id,
            tenant_id=5,
            email=f"{login_id}@example.com",
            display_name=login_id,
            role="USER",
            login_id=login_id,
        )

    def test_export_is_saved_inside_owner_workspace(self):
        scope = self.storage.create_scope(self.user_a)
        result = {"job_description": JobDescription(job_title="Engineer")}
        export = self.service.build_excel_report(self.user_a, scope, result)
        self.assertEqual(export.filename, "Engineer_Report.xlsx")
        self.assertEqual(export.data, b"private-excel-content")
        self.assertTrue(export.stored_file.absolute_path.exists())
        self.assertIn("tenant_5/user_11", export.stored_file.relative_path)
        self.assertEqual(self.service.read_export(self.user_a, export.stored_file), export.data)

    def test_other_user_cannot_read_export(self):
        scope = self.storage.create_scope(self.user_a)
        export = self.service.build_excel_report(
            self.user_a,
            scope,
            {"job_description": JobDescription(job_title="Engineer")},
        )
        with self.assertRaises(PermissionError):
            self.service.read_export(self.user_b, export.stored_file)


if __name__ == "__main__":
    unittest.main()
