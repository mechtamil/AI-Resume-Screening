import unittest
from services.upload_service import UploadService


class FakeUpload:
    def __init__(self, name, content=b"data"):
        self.name = name
        self._content = content
        self.size = len(content)
    def getbuffer(self):
        return memoryview(self._content)


class UploadServiceTests(unittest.TestCase):
    def test_safe_name_blocks_path_traversal_and_adds_unique_suffix(self):
        name = UploadService._safe_name("../../Resume Test.PDF")
        self.assertNotIn("..", name)
        self.assertTrue(name.endswith(".pdf"))
        self.assertIn("Resume Test", name)

    def test_invalid_extension_rejected(self):
        with self.assertRaises(ValueError):
            UploadService.save_resume(FakeUpload("bad.exe"))


if __name__ == "__main__": unittest.main()
