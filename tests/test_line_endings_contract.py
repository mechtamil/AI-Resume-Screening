"""Repository contracts for deterministic cross-platform source line endings."""
from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class LineEndingsContractTests(unittest.TestCase):
    def test_extensionless_version_file_is_forced_to_lf(self) -> None:
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("VERSION text eol=lf", attributes)

    def test_example_configuration_files_are_forced_to_lf(self) -> None:
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("*.example text eol=lf", attributes)


if __name__ == "__main__":
    unittest.main()
