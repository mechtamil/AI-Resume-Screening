import tempfile
import unittest
from pathlib import Path
from database.database import Database


class DatabaseTests(unittest.TestCase):
    def test_create_tables_in_temporary_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.db"
            db = Database(path)
            db.create_tables()
            names = {row[0] for row in db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            db.close()
            self.assertTrue({"recruitment_projects", "candidates", "resumes"}.issubset(names))


if __name__ == "__main__":
    unittest.main()
