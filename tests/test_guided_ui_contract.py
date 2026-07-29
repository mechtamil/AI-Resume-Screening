"""Static contracts for the guided, non-duplicated Streamlit workspace."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class GuidedUiContractTests(unittest.TestCase):
    def test_screening_page_exposes_templates_and_common_formats(self):
        source = (ROOT / "ui" / "resume_screening.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("Download Job Description Excel Template", source)
        self.assertIn("Download Supplemental Skill List Template", source)
        self.assertIn("SUPPORTED_JD_TYPES", source)

    def test_screening_uses_single_results_navigation_path(self):
        source = (ROOT / "ui" / "resume_screening.py").read_text(encoding="utf-8")
        app_source = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(source)
        ast.parse(app_source)
        self.assertNotIn("View Ranked Results", source)
        self.assertNotIn('key="screening_view_results"', source)
        self.assertIn("Use the Results action below", source)
        self.assertIn("render_workflow_navigation(", app_source)

    def test_sidebar_has_one_profile_card_dark_mode_and_bottom_signout_key(self):
        auth_source = (ROOT / "ui" / "authentication.py").read_text(encoding="utf-8")
        theme_source = (ROOT / "ui" / "theme.py").read_text(encoding="utf-8")
        ast.parse(auth_source)
        ast.parse(theme_source)
        self.assertIn("sidebar_user_card_html", auth_source)
        self.assertIn('key="dark_mode"', auth_source)
        self.assertIn('key="sidebar_sign_out"', auth_source)
        self.assertIn(".st-key-sidebar_sign_out", theme_source)

    def test_home_contains_direct_operational_actions(self):
        source = (ROOT / "ui" / "home.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("Start Resume Screening", source)
        self.assertIn("Open Candidate Database", source)
        self.assertIn("Open Results", source)


if __name__ == "__main__":
    unittest.main()
