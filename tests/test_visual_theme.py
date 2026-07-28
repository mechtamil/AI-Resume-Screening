"""Static validation for the ALTEN visual system and simplified login."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

from config import brand
from ui.brand_components import login_visual_html, page_header_html
from ui.theme import build_theme_css


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class VisualThemeTests(unittest.TestCase):
    def test_verified_brand_tokens_are_centralized(self):
        self.assertEqual(brand.ALTEN_NAVY, "#043962")
        self.assertEqual(brand.ALTEN_BLUE, "#008BD2")
        self.assertEqual(brand.ALTEN_LIGHT_BLUE, "#7ECBEE")
        self.assertEqual(brand.ALTEN_RED, "#E30513")
        self.assertEqual(brand.ALTEN_PALE_GREY, "#E6E6E9")

    def test_theme_has_motion_depth_responsiveness_and_accessibility(self):
        css = build_theme_css()
        for marker in (
            "@keyframes ros-float",
            "@keyframes ros-shimmer",
            "backdrop-filter",
            "linear-gradient",
            "@media (max-width: 760px)",
            "prefers-reduced-motion: reduce",
        ):
            self.assertIn(marker, css)

    def test_brand_components_render_visual_story(self):
        visual = login_visual_html()
        self.assertIn("ros-login-visual", visual)
        self.assertIn("RecruitOS", visual)
        self.assertIn("AI-powered", visual)
        self.assertIn("<img", visual)

        header = page_header_html(
            title="Administration",
            eyebrow="Identity control",
            description="Provision access securely.",
        )
        self.assertIn("Administration", header)
        self.assertIn("ros-page-hero", header)

    def test_login_source_contains_only_user_id_password_and_forgot_password(self):
        source_path = PROJECT_ROOT / "ui" / "authentication.py"
        source = source_path.read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn('"User ID"', source)
        self.assertIn('"Password"', source)
        self.assertIn('"Forgot Password?"', source)
        self.assertNotIn('st.selectbox("Organization', source)
        self.assertNotIn('st.selectbox("Country', source)
        self.assertNotIn('st.selectbox("Region', source)
        self.assertNotIn("Create account", source.casefold())


if __name__ == "__main__":
    unittest.main()
