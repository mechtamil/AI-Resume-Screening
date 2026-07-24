import unittest
from config.sheet_names import ALL_SHEETS
from services.master_repository import MasterRepository


class MasterRepositoryTests(unittest.TestCase):
    def test_workbook_structure(self):
        self.assertTrue(MasterRepository.validate_workbook())
        self.assertTrue(set(ALL_SHEETS).issubset(MasterRepository.list_sheets()))
        self.assertIn("Skills", MasterRepository.workbook_info())


if __name__ == "__main__":
    unittest.main()
