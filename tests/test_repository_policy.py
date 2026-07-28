"""Tests for RecruitOS repository-policy enforcement."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.repository_policy import RepositoryPolicy


class RepositoryPolicyTests(unittest.TestCase):
    def _create_minimum_source(self, root: Path) -> None:
        for relative in RepositoryPolicy.REQUIRED_FILES:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"placeholder\n")
        for relative in ("uploads/.gitkeep", "output/.gitkeep", "temp/.gitkeep", "logs/.gitkeep", "Resume/.gitkeep"):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")

    def test_minimum_clean_source_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._create_minimum_source(root)
            findings = RepositoryPolicy(root).validate()
            self.assertEqual(RepositoryPolicy.errors(findings), [])

    def test_sensitive_runtime_and_package_files_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._create_minimum_source(root)
            forbidden = {
                ".env": b"SECRET=value",
                ".streamlit/secrets.toml": b"token='secret'",
                "database/recruitos.db": b"sqlite",
                "Resume/candidate.pdf": b"private",
                "uploads/private/resume.pdf": b"private",
                "output/report.xlsx": b"private",
                "database/__pycache__/database.pyc": b"cache",
                "PACKAGE_MANIFEST_SHA256.txt": b"manifest",
                "sprint.zip": b"zip",
                "Master_Data/skills_master.xlsx": b"legacy",
            }
            for relative, payload in forbidden.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)

            policy = RepositoryPolicy(root)
            selected = policy.filesystem_files() + [
                "database/__pycache__/database.pyc"
            ]
            findings = policy.validate(selected)
            codes = {finding.code for finding in RepositoryPolicy.errors(findings)}
            self.assertIn("SECRET_FILE_TRACKED", codes)
            self.assertIn("DATABASE_TRACKED", codes)
            self.assertIn("RUNTIME_DATA_TRACKED", codes)
            self.assertIn("PYTHON_CACHE_TRACKED", codes)
            self.assertIn("PACKAGE_ARTIFACT_TRACKED", codes)
            self.assertIn("LEGACY_MASTER_TRACKED", codes)

    def test_central_workbook_and_safe_examples_are_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._create_minimum_source(root)
            (root / ".env.example").write_text("KEY=placeholder\n", encoding="utf-8")
            (root / "JD").mkdir(exist_ok=True)
            (root / "JD" / "sample_jd.txt").write_text("Sample only", encoding="utf-8")
            (root / "SOURCE_MANIFEST_SHA256.txt").write_text("hash  app.py\n", encoding="utf-8")
            findings = RepositoryPolicy(root).validate()
            self.assertEqual(RepositoryPolicy.errors(findings), [])


if __name__ == "__main__":
    unittest.main()
