"""Tests for deterministic clean RecruitOS source releases."""
from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.build_clean_release import build_clean_release, sha256_bytes
from tools.repository_policy import RepositoryPolicy


class BuildCleanReleaseTests(unittest.TestCase):
    def _source_tree(self, root: Path) -> list[str]:
        files: dict[str, bytes] = {
            "app.py": b"print('RecruitOS')\n",
            "VERSION": b"9.9.9\n",
            "requirements.txt": b"streamlit\n",
            ".gitignore": b"*.db\n",
            "Master_Data/RecruitOS_Configuration.xlsx": b"workbook",
            "tests/test_example.py": b"import unittest\n",
            "uploads/.gitkeep": b"",
        }
        for relative, payload in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        return sorted(files)

    def test_release_contains_only_selected_source_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selected = self._source_tree(root)
            runtime = root / "uploads/private/candidate.pdf"
            runtime.parent.mkdir(parents=True, exist_ok=True)
            runtime.write_bytes(b"private")
            output = root / "release.zip"

            build_clean_release(
                root,
                output,
                files=selected,
                require_clean_git=False,
            )

            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                self.assertIn("RecruitOS-v9.9.9/app.py", names)
                self.assertIn("RecruitOS-v9.9.9/SOURCE_MANIFEST_SHA256.txt", names)
                self.assertNotIn("RecruitOS-v9.9.9/uploads/private/candidate.pdf", names)
                manifest = archive.read(
                    "RecruitOS-v9.9.9/SOURCE_MANIFEST_SHA256.txt"
                ).decode("utf-8")
                self.assertIn(sha256_bytes(b"print('RecruitOS')\n"), manifest)

    def test_release_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selected = self._source_tree(root)
            first = root / "first.zip"
            second = root / "second.zip"
            build_clean_release(root, first, files=selected, require_clean_git=False)
            build_clean_release(root, second, files=selected, require_clean_git=False)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_policy_violation_blocks_release(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selected = self._source_tree(root)
            secret = root / ".env"
            secret.write_text("TOKEN=secret", encoding="utf-8")
            selected.append(".env")
            with self.assertRaisesRegex(ValueError, "SECRET_FILE_TRACKED"):
                build_clean_release(
                    root,
                    root / "blocked.zip",
                    files=selected,
                    require_clean_git=False,
                )


if __name__ == "__main__":
    unittest.main()
