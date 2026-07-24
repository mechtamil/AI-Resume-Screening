import unittest
import pandas as pd
from services.base_repository import BaseRepository


class BaseRepositoryTests(unittest.TestCase):
    def test_common_dataframe_utilities(self):
        frame = pd.DataFrame({"Name": ["Python", "SQL", "Python", None], "Active": ["Yes", "No", "Yes", "Yes"]})
        self.assertEqual(BaseRepository.normalize_text(" Python "), "python")
        self.assertEqual(BaseRepository.clean_list(["Python", "python", "", None, "SQL"]), ["python", "sql"])
        self.assertTrue(BaseRepository.exists(frame, "Name", "python"))
        self.assertEqual(len(BaseRepository.filter_active(frame)), 3)
        self.assertEqual(BaseRepository.total_records(frame), 4)


if __name__ == "__main__":
    unittest.main()
