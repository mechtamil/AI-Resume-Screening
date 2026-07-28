import tempfile
import unittest
from pathlib import Path

from models.security_context import SecurityContext
from services.secure_storage_service import SecureStorageService
from services.upload_service import UploadService


class FakeUpload:
    def __init__(self, name, content=b"data"):
        self.name = name
        self._content = content
        self.size = len(content)

    def getbuffer(self):
        return memoryview(self._content)


class UploadServiceTests(unittest.TestCase):
    def setUp(self):
        self.context = SecurityContext(
            user_id=10,
            tenant_id=20,
            email="user@example.com",
            display_name="User",
            role="USER",
            login_id="6276",
        )

    def tearDown(self):
        UploadService.reset_storage()

    def test_safe_name_blocks_path_traversal(self):
        name = UploadService._safe_name("../../Resume Test.PDF")
        self.assertNotIn("..", name)
        self.assertTrue(name.endswith(".pdf"))
        self.assertIn("Resume Test", name)

    def test_invalid_extension_rejected_in_private_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            UploadService.configure_storage(
                SecureStorageService(
                    uploads_root=root / "uploads",
                    temp_root=root / "temp",
                    output_root=root / "output",
                )
            )
            scope = UploadService.create_workspace(self.context)
            with self.assertRaises(ValueError):
                UploadService.save_resume(
                    self.context,
                    scope,
                    FakeUpload("bad.exe"),
                )

    def test_saved_upload_path_contains_owner_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            UploadService.configure_storage(
                SecureStorageService(
                    uploads_root=root / "uploads",
                    temp_root=root / "temp",
                    output_root=root / "output",
                )
            )
            scope = UploadService.create_workspace(self.context)
            stored = UploadService.save_resume(
                self.context,
                scope,
                FakeUpload("candidate.pdf", b"private resume"),
            )
            self.assertTrue(stored.absolute_path.exists())
            self.assertIn("tenant_20", stored.relative_path)
            self.assertIn("user_10", stored.relative_path)
            self.assertIn(f"workspace_{scope.workspace_id}", stored.relative_path)


if __name__ == "__main__":
    unittest.main()
