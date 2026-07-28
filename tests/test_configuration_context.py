"""ConfigurationContext and MasterRepository isolation tests."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path

from openpyxl import load_workbook

from config.paths import CONFIGURATION_WORKBOOK
from models.configuration_version import ConfigurationSelection
from services.configuration_context import ConfigurationContext
from services.master_repository import MasterRepository
from services.skill_repository import SkillRepository


def _workbook_with_skill(directory: Path, name: str, skill: str) -> Path:
    path = directory / name
    shutil.copy2(CONFIGURATION_WORKBOOK, path)
    workbook = load_workbook(path)
    sheet = workbook["Skills"]
    headers = [cell.value for cell in sheet[1]]
    values = {
        "Skill": skill,
        "Category": "Tenant Test",
        "Sub Category": "Isolation",
        "Synonyms": f"{skill} Alias",
        "Active": "Yes",
    }
    sheet.append([values.get(header, "") for header in headers])
    workbook.save(path)
    return path


def _selection(tenant_id: int, path: Path) -> ConfigurationSelection:
    content = path.read_bytes()
    return ConfigurationSelection(
        tenant_id=tenant_id,
        workbook_path=path,
        source="tenant_version",
        version_id=tenant_id,
        version_number=1,
        configuration_key=f"tenant-{tenant_id}",
        sha256=sha256(content).hexdigest(),
        file_size=len(content),
    )


class ConfigurationContextTests(unittest.TestCase):
    def tearDown(self) -> None:
        MasterRepository.clear_cache()

    def test_two_tenant_workbooks_do_not_share_repository_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alpha = _workbook_with_skill(root, "alpha.xlsx", "Alpha Tenant Skill")
            beta = _workbook_with_skill(root, "beta.xlsx", "Beta Tenant Skill")

            with ConfigurationContext.activate(_selection(11, alpha)):
                alpha_skills = SkillRepository().get_all_skills()
                self.assertIn("Alpha Tenant Skill", alpha_skills)
                self.assertNotIn("Beta Tenant Skill", alpha_skills)

            with ConfigurationContext.activate(_selection(22, beta)):
                beta_skills = SkillRepository().get_all_skills()
                self.assertIn("Beta Tenant Skill", beta_skills)
                self.assertNotIn("Alpha Tenant Skill", beta_skills)

            default_skills = SkillRepository().get_all_skills()
            self.assertNotIn("Alpha Tenant Skill", default_skills)
            self.assertNotIn("Beta Tenant Skill", default_skills)

    def test_nested_context_restores_previous_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alpha = _workbook_with_skill(root, "alpha.xlsx", "Alpha Tenant Skill")
            beta = _workbook_with_skill(root, "beta.xlsx", "Beta Tenant Skill")
            alpha_selection = _selection(11, alpha)
            beta_selection = _selection(22, beta)

            with ConfigurationContext.activate(alpha_selection):
                self.assertEqual(ConfigurationContext.current(), alpha_selection)
                with ConfigurationContext.activate(beta_selection):
                    self.assertEqual(ConfigurationContext.current(), beta_selection)
                self.assertEqual(ConfigurationContext.current(), alpha_selection)

            self.assertIsNone(ConfigurationContext.current())


if __name__ == "__main__":
    unittest.main()
