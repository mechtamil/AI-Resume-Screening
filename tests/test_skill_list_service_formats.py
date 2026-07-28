"""Tests for mandatory/preferred supplemental skill parsing."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from services.skill_list_service import SkillListService


class SkillListServiceFormatTests(unittest.TestCase):
    def test_excel_distinguishes_mandatory_and_preferred_skills(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "skills.xlsx"
            pd.DataFrame(
                [
                    {"Skill": "Python", "Requirement Type": "Mandatory"},
                    {"Skill": "SQL", "Requirement Type": "Preferred"},
                    {"Skill": "Docker", "Requirement Type": "nice to have"},
                ]
            ).to_excel(path, index=False, sheet_name="Skills")

            result = SkillListService.read_requirements(path)

            self.assertIn("Python", result["mandatory"])
            self.assertIn("SQL", result["preferred"])
            self.assertIn("Docker", result["preferred"])

    def test_text_defaults_to_mandatory(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "skills.txt"
            path.write_text("Python, SQL\nDocker", encoding="utf-8")
            result = SkillListService.read_requirements(path)
            self.assertEqual(result["preferred"], [])
            self.assertEqual(result["mandatory"], ["Python", "SQL", "Docker"])


if __name__ == "__main__":
    unittest.main()
