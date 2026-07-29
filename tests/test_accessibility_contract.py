"""Contracts for RecruitOS mode-safe visibility and accessibility."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

from ui.accessibility import build_accessibility_css


ROOT = Path(__file__).resolve().parent.parent


class AccessibilityContractTests(unittest.TestCase):
    def test_login_copy_is_readable_without_restyling_login_layout(self) -> None:
        css = build_accessibility_css()
        self.assertIn(".ros-login-shell p.ros-login-copy", css)
        self.assertIn("color: rgba(255, 255, 255, .90) !important", css)
        self.assertNotIn(".ros-login-shell {", css)
        self.assertNotIn(".ros-page-hero {", css)

    def test_primary_actions_force_white_nested_labels(self) -> None:
        css = build_accessibility_css()
        self.assertIn('button[kind="primary"]:not(:disabled)', css)
        self.assertIn('[data-testid="stBaseButton-primary"]:not(:disabled)', css)
        self.assertIn("color: #FFFFFF !important", css)
        self.assertIn("fill: currentColor !important", css)

    def test_secondary_and_download_actions_force_navy_labels(self) -> None:
        css = build_accessibility_css()
        self.assertIn(".stDownloadButton > button:not(:disabled)", css)
        self.assertIn('[data-testid="stDownloadButton"] button:not(:disabled)', css)
        self.assertIn('[data-testid="stBaseButton-secondary"]:not(:disabled)', css)
        self.assertIn("color: #043962 !important", css)
        self.assertIn("linear-gradient(145deg, #FFFFFF, #EEF6FC)", css)

    def test_disabled_actions_remain_readable(self) -> None:
        css = build_accessibility_css()
        self.assertIn("button:disabled", css)
        self.assertIn("cursor: not-allowed !important", css)
        self.assertIn("opacity: 1 !important", css)

    def test_every_file_uploader_has_dark_instructions_and_white_button_text(self) -> None:
        css = build_accessibility_css()
        self.assertIn('[data-testid="stFileUploaderDropzoneInstructions"]', css)
        self.assertIn('[data-testid="stFileUploaderDropzone"] button', css)
        self.assertIn("color: #043962 !important", css)
        self.assertIn("color: #FFFFFF !important", css)

    def test_expander_header_uses_mode_aware_surface_and_text(self) -> None:
        css = build_accessibility_css()
        self.assertIn('[data-testid="stExpander"] summary', css)
        self.assertIn("background: var(--ros-panel-strong) !important", css)
        self.assertIn("color: var(--ros-text) !important", css)

    def test_tabs_have_rounded_rail_selected_and_inactive_states(self) -> None:
        css = build_accessibility_css()
        self.assertIn('[data-testid="stTabs"] [role="tablist"]', css)
        self.assertIn("border-radius: 18px !important", css)
        self.assertIn('button[role="tab"][aria-selected="true"]', css)
        self.assertIn("color: var(--ros-text) !important", css)
        self.assertIn("inset 0 -3px 0 var(--alten-yellow)", css)

    def test_form_placeholders_and_list_options_follow_mode_tokens(self) -> None:
        css = build_accessibility_css()
        self.assertIn("input::placeholder", css)
        self.assertIn('[data-baseweb="popover"] [role="option"]', css)
        self.assertIn("color: var(--ros-muted) !important", css)
        self.assertIn("color: var(--ros-text) !important", css)

    def test_sidebar_caption_and_navigation_are_explicitly_readable(self) -> None:
        css = build_accessibility_css()
        self.assertIn('[data-testid="stCaptionContainer"]', css)
        self.assertIn('color: rgba(255, 255, 255, .76) !important', css)
        self.assertIn('[data-testid="stRadio"] label *', css)
        self.assertIn('color: rgba(255, 255, 255, .94) !important', css)

    def test_signout_has_blue_background_and_white_nested_text(self) -> None:
        css = build_accessibility_css()
        self.assertIn(".st-key-sidebar_sign_out", css)
        self.assertIn("#0070C0", css)
        self.assertIn("#008BD2", css)
        self.assertIn("color: #FFFFFF !important", css)

    def test_sidebar_footer_is_not_sticky_over_navigation(self) -> None:
        css = build_accessibility_css()
        self.assertIn(":has(.ros-sidebar-footer-marker)", css)
        self.assertIn("position: static !important", css)

    def test_accessibility_overrides_are_loaded_after_base_theme(self) -> None:
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(source)
        theme_index = source.index("apply_alten_theme(")
        accessibility_index = source.index("apply_accessibility_overrides()")
        self.assertLess(theme_index, accessibility_index)

    def test_screening_explains_how_to_enable_analysis(self) -> None:
        source = (ROOT / "ui" / "resume_screening.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("Before analysis:", source)
        self.assertIn("upload a Job Description", source)
        self.assertIn("upload at least one candidate resume", source)
        self.assertIn('key="analyze_save_candidates"', source)


if __name__ == "__main__":
    unittest.main()
