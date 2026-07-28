"""Security tests for tenant/user/session isolated file storage."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from models.security_context import SecurityContext
from services.secure_storage_service import SecureStorageService


class FakeUpload:
    def __init__(self, name: str, content: bytes):
        self.name = name
        self._content = content
        self.size = len(content)

    def getbuffer(self):
        return memoryview(self._content)


class SecureStorageServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        root = Path(self.temp_directory.name)
        self.storage = SecureStorageService(
            uploads_root=root / "uploads",
            temp_root=root / "temp",
            output_root=root / "output",
        )
        self.user_a = self._context(101, 7, "A-101")
        self.user_b = self._context(202, 7, "B-202")
        self.other_tenant = self._context(303, 8, "C-303")

    def tearDown(self):
        self.temp_directory.cleanup()

    @staticmethod
    def _context(user_id: int, tenant_id: int, login_id: str) -> SecurityContext:
        return SecurityContext(
            user_id=user_id,
            tenant_id=tenant_id,
            email=f"{login_id.lower()}@example.com",
            display_name=login_id,
            role="USER",
            login_id=login_id,
        )

    def test_uploads_are_partitioned_by_tenant_user_and_workspace(self):
        scope_a = self.storage.create_scope(self.user_a)
        scope_b = self.storage.create_scope(self.user_b, scope_a.workspace_id)
        stored_a = self.storage.save_upload(
            self.user_a,
            scope_a,
            "resumes",
            FakeUpload("candidate.pdf", b"user-a"),
            (".pdf",),
        )
        stored_b = self.storage.save_upload(
            self.user_b,
            scope_b,
            "resumes",
            FakeUpload("candidate.pdf", b"user-b"),
            (".pdf",),
        )
        self.assertNotEqual(stored_a.absolute_path, stored_b.absolute_path)
        self.assertEqual(self.storage.read_owned_file(self.user_a, stored_a.absolute_path), b"user-a")
        self.assertEqual(self.storage.read_owned_file(self.user_b, stored_b.absolute_path), b"user-b")

    def test_user_cannot_read_delete_or_list_another_users_files(self):
        scope_a = self.storage.create_scope(self.user_a)
        stored = self.storage.save_upload(
            self.user_a,
            scope_a,
            "job_description",
            FakeUpload("jd.txt", b"private-jd"),
            (".txt",),
        )
        with self.assertRaises(PermissionError):
            self.storage.read_owned_file(self.user_b, stored.absolute_path)
        with self.assertRaises(PermissionError):
            self.storage.delete_owned_file(self.user_b, stored.absolute_path)
        forged_scope = type(scope_a)(
            tenant_id=self.user_b.tenant_id,
            user_id=self.user_b.user_id,
            workspace_id=scope_a.workspace_id,
        )
        self.assertEqual(self.storage.list_workspace_files(self.user_b, forged_scope), [])
        self.assertTrue(stored.absolute_path.exists())

    def test_other_tenant_cannot_access_file_even_with_known_absolute_path(self):
        scope = self.storage.create_scope(self.user_a)
        stored = self.storage.save_export_bytes(
            self.user_a,
            scope,
            "report.xlsx",
            b"xlsx-bytes",
        )
        with self.assertRaises(PermissionError):
            self.storage.read_owned_file(self.other_tenant, stored.absolute_path)

    def test_path_traversal_filename_is_sanitized_and_content_is_hashed(self):
        scope = self.storage.create_scope(self.user_a)
        stored = self.storage.save_upload(
            self.user_a,
            scope,
            "resumes",
            FakeUpload("../../../../secret.PDF", b"content"),
            (".pdf",),
        )
        self.assertNotIn("..", stored.stored_name)
        self.assertEqual(stored.original_name, "secret.pdf")
        self.assertEqual(
            stored.sha256,
            "ed7002b439e9ac845f22357d822bac1444730fbdb6016d3ec9432297b9ec9f73",
        )

    def test_cleanup_and_workspace_delete_are_owner_scoped(self):
        scope_a = self.storage.create_scope(self.user_a)
        scope_b = self.storage.create_scope(self.user_b)
        temp_a = self.storage.save_temp_bytes(self.user_a, scope_a, "parse.txt", b"a")
        upload_a = self.storage.save_upload(
            self.user_a,
            scope_a,
            "resumes",
            FakeUpload("a.pdf", b"a"),
            (".pdf",),
        )
        upload_b = self.storage.save_upload(
            self.user_b,
            scope_b,
            "resumes",
            FakeUpload("b.pdf", b"b"),
            (".pdf",),
        )
        self.storage.cleanup_temp_workspace(self.user_a, scope_a)
        self.assertFalse(temp_a.absolute_path.exists())
        self.assertTrue(upload_a.absolute_path.exists())
        self.storage.delete_workspace(self.user_a, scope_a)
        self.assertFalse(upload_a.absolute_path.exists())
        self.assertTrue(upload_b.absolute_path.exists())

    def test_scope_ownership_is_required_for_write(self):
        scope_a = self.storage.create_scope(self.user_a)
        with self.assertRaises(PermissionError):
            self.storage.save_temp_bytes(self.user_b, scope_a, "x.txt", b"x")


if __name__ == "__main__":
    unittest.main()
