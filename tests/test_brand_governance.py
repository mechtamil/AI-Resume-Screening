"""Contracts that keep ALTEN brand governance durable in the repository."""
from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GOVERNANCE = ROOT / "docs" / "ALTEN_UI_GOVERNANCE.md"


class BrandGovernanceTests(unittest.TestCase):
    def test_official_brandbook_is_mandatory_authority(self) -> None:
        text = GOVERNANCE.read_text(encoding="utf-8")
        self.assertIn("Brandbook-ALTEN-2025-EN.pdf", text)
        self.assertIn("source of truth", text)
        self.assertIn("must be reviewed", text)

    def test_external_ui_references_cannot_override_alten(self) -> None:
        text = GOVERNANCE.read_text(encoding="utf-8")
        self.assertIn("UI/UX Pro Max", text)
        self.assertIn("21st.dev", text)
        self.assertIn("supporting references only", text)

    def test_governance_contains_accessibility_and_privacy_controls(self) -> None:
        text = GOVERNANCE.read_text(encoding="utf-8")
        for marker in (
            "WCAG AA",
            "keyboard focus",
            "prefers-reduced-motion",
            "candidate data",
            "Disabled actions",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
