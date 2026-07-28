"""Tests for environment and Streamlit-secret deployment settings."""
from __future__ import annotations

import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from config import settings


class SettingsConfigurationTests(unittest.TestCase):
    def test_environment_value_has_priority(self) -> None:
        fake_streamlit = SimpleNamespace(secrets={"RECRUITOS_TEST_VALUE": "secret"})
        with (
            patch.dict(os.environ, {"RECRUITOS_TEST_VALUE": "environment"}),
            patch.dict(sys.modules, {"streamlit": fake_streamlit}),
        ):
            self.assertEqual(
                settings._deployment_value("RECRUITOS_TEST_VALUE"),
                "environment",
            )

    def test_streamlit_secret_is_used_when_environment_is_absent(self) -> None:
        fake_streamlit = SimpleNamespace(secrets={"RECRUITOS_TEST_VALUE": "secret"})
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.dict(sys.modules, {"streamlit": fake_streamlit}),
        ):
            self.assertEqual(
                settings._deployment_value("RECRUITOS_TEST_VALUE"),
                "secret",
            )

    def test_missing_value_uses_default(self) -> None:
        fake_streamlit = SimpleNamespace(secrets={})
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.dict(sys.modules, {"streamlit": fake_streamlit}),
        ):
            self.assertEqual(
                settings._deployment_value("RECRUITOS_NOT_DEFINED", "fallback"),
                "fallback",
            )


if __name__ == "__main__":
    unittest.main()
