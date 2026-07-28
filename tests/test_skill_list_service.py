import tempfile
import unittest
from pathlib import Path
from services.skill_list_service import SkillListService


class SkillListServiceTests(unittest.TestCase):
    def test_text_skill_list_preserves_unknown_and_normalizes_known(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "skills.txt"
            path.write_text("python\nCustom Requirement\n", encoding="utf-8")
            values = SkillListService.read_skills(path)
            self.assertIn("Python", values)
            self.assertIn("Custom Requirement", values)


if __name__ == "__main__": unittest.main()
