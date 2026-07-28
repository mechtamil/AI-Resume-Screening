import unittest
from config.paths import CONFIGURATION_WORKBOOK, PROJECT_ROOT, UPLOAD_JD_DIR, UPLOAD_RESUME_DIR


class PathsTests(unittest.TestCase):
    def test_paths_are_project_relative_and_runtime_dirs_exist(self):
        self.assertTrue(PROJECT_ROOT.exists())
        self.assertTrue(CONFIGURATION_WORKBOOK.exists())
        self.assertTrue(UPLOAD_JD_DIR.exists())
        self.assertTrue(UPLOAD_RESUME_DIR.exists())


if __name__ == "__main__": unittest.main()
