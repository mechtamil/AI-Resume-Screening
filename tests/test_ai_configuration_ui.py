"""Static UI contracts for the AI registry and tenant-policy workspace."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class AIConfigurationUIContractTests(unittest.TestCase):
    def test_configuration_page_exposes_ai_policy_tab(self) -> None:
        source = (ROOT / "ui" / "configuration_management.py").read_text(
            encoding="utf-8"
        )
        ast.parse(source)
        self.assertIn("AI Provider & Model Policy", source)
        self.assertIn("show_ai_configuration(context)", source)

    def test_ai_ui_never_accepts_or_displays_api_keys(self) -> None:
        source = (ROOT / "ui" / "ai_configuration.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertNotIn('st.text_input("API Key', source)
        self.assertNotIn('type="password"', source)
        self.assertNotIn("AI_OPENAI_API_KEY", source)
        self.assertIn("No credential was stored", source)

    def test_ai_ui_documents_default_denial_and_external_transfer_control(self) -> None:
        source = (ROOT / "ui" / "ai_configuration.py").read_text(encoding="utf-8")
        self.assertIn("AI execution is denied by default", source)
        self.assertIn("Allow approved content to leave the local environment", source)
        self.assertIn("Prompt text, candidate text", source)

    def test_ai_gateway_is_not_integrated_into_screening_in_this_sprint(self) -> None:
        for relative in (
            "services/processing_service.py",
            "ui/resume_screening.py",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("AIProviderGateway", source)


if __name__ == "__main__":
    unittest.main()
