"""End-to-end screening isolation for tenant-specific master data."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from openpyxl import load_workbook

from config.paths import CONFIGURATION_WORKBOOK
from services.processing_service import ProcessingService
from services.tenant_configuration_service import TenantConfigurationService
from tests.security_test_utils import create_context, create_owner_context


def _workbook(root: Path, name: str, skill: str) -> Path:
    path = root / name
    shutil.copy2(CONFIGURATION_WORKBOOK, path)
    workbook = load_workbook(path)
    sheet = workbook["Skills"]
    headers = [cell.value for cell in sheet[1]]
    values = {
        "Skill": skill,
        "Category": "AI Ready Taxonomy",
        "Sub Category": "Tenant Specific",
        "Synonyms": f"{skill} Alias",
        "Active": "Yes",
    }
    sheet.append([values.get(header, "") for header in headers])
    workbook.save(path)
    return path


class ConfigurationScreeningIsolationTests(unittest.TestCase):
    def test_screening_uses_only_authenticated_tenant_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database_path = root / "screening.db"
            owner = create_owner_context(database_path)
            alpha_user = create_context(database_path, "alpha@example.com", "Alpha User")
            beta_user = create_context(database_path, "beta@example.com", "Beta User")
            service = TenantConfigurationService(
                database_path,
                private_root=root / "private-configurations",
                system_default_path=CONFIGURATION_WORKBOOK,
            )
            alpha_book = _workbook(root, "alpha.xlsx", "AlphaSemanticSkill")
            beta_book = _workbook(root, "beta.xlsx", "BetaSemanticSkill")
            service.upload_version(
                owner,
                target_user_id=alpha_user.user_id,
                file_name="alpha.xlsx",
                content=alpha_book.read_bytes(),
                activate=True,
            )
            service.upload_version(
                owner,
                target_user_id=beta_user.user_id,
                file_name="beta.xlsx",
                content=beta_book.read_bytes(),
                activate=True,
            )

            jd = root / "jd.txt"
            resume = root / "resume.txt"
            jd.write_text(
                """Job Title: AI Documentation Engineer\nExperience: 1-3 years\nMandatory Skills\nAlphaSemanticSkill\n""",
                encoding="utf-8",
            )
            resume.write_text(
                """Candidate Alpha\nalpha@example.com\nTotal Experience: 2 years\nTechnical Skills\nAlphaSemanticSkill\n""",
                encoding="utf-8",
            )

            alpha_result = ProcessingService.process_documents(
                jd,
                [resume],
                security_context=alpha_user,
                configuration_service=service,
            )
            beta_result = ProcessingService.process_documents(
                jd,
                [resume],
                security_context=beta_user,
                configuration_service=service,
            )

            self.assertIn(
                "AlphaSemanticSkill",
                alpha_result["candidates"][0].technical_skills,
            )
            self.assertNotIn(
                "AlphaSemanticSkill",
                beta_result["candidates"][0].technical_skills,
            )
            self.assertEqual(alpha_result["configuration"]["source"], "tenant_version")
            self.assertEqual(beta_result["configuration"]["source"], "tenant_version")
            self.assertNotEqual(
                alpha_result["configuration"]["sha256"],
                beta_result["configuration"]["sha256"],
            )


if __name__ == "__main__":
    unittest.main()
