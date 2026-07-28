import unittest
from utils.file_utils import get_extension, is_supported, validate


class FakeUpload:
    def __init__(self, name="resume.pdf", size=100):
        self.name = name
        self.size = size


class FileUtilsTests(unittest.TestCase):
    def test_extension_and_validation(self):
        self.assertEqual(get_extension("Resume.PDF"), ".pdf")
        self.assertTrue(is_supported("resume.pdf"))
        self.assertEqual(validate(FakeUpload()), [])
        self.assertTrue(validate(FakeUpload("malware.exe")))


if __name__ == "__main__":
    unittest.main()
