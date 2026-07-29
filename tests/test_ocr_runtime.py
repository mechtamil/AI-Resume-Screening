"""Tests for deployment-configured and PATH-based Tesseract discovery."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from services.ocr_runtime import configure_pytesseract, resolve_tesseract_command


ROOT = Path(__file__).resolve().parent.parent


class OcrRuntimeTests(unittest.TestCase):
    def test_configured_executable_path_is_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "tesseract.exe"
            executable.write_bytes(b"test-runtime")
            resolved = resolve_tesseract_command(str(executable))
            self.assertEqual(Path(resolved), executable.resolve())

    def test_invalid_configured_path_fails_clearly(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "RECRUITOS_TESSERACT_CMD"):
            resolve_tesseract_command("missing/tesseract.exe")

    def test_command_name_can_be_resolved_through_path(self) -> None:
        with patch("services.ocr_runtime.shutil.which", return_value="/usr/bin/tesseract"):
            self.assertEqual(
                resolve_tesseract_command("tesseract"),
                "/usr/bin/tesseract",
            )

    def test_empty_configuration_falls_back_to_path(self) -> None:
        with patch("services.ocr_runtime.shutil.which", return_value="/usr/bin/tesseract"):
            self.assertEqual(resolve_tesseract_command(""), "/usr/bin/tesseract")

    def test_missing_runtime_returns_none_until_ocr_is_requested(self) -> None:
        with patch("services.ocr_runtime.shutil.which", return_value=None):
            self.assertIsNone(resolve_tesseract_command())

    def test_configure_pytesseract_sets_resolved_command(self) -> None:
        fake = SimpleNamespace(pytesseract=SimpleNamespace(tesseract_cmd=""))
        with patch(
            "services.ocr_runtime.resolve_tesseract_command",
            return_value="/opt/tesseract",
        ):
            command = configure_pytesseract(fake)
        self.assertEqual(command, "/opt/tesseract")
        self.assertEqual(fake.pytesseract.tesseract_cmd, "/opt/tesseract")

    def test_no_user_specific_tesseract_path_is_hardcoded(self) -> None:
        tracked_sources = (
            ROOT / "config" / "settings.py",
            ROOT / "parser" / "image_reader.py",
            ROOT / "services" / "ocr_runtime.py",
        )
        combined = "\n".join(path.read_text(encoding="utf-8") for path in tracked_sources)
        self.assertNotIn("A481562", combined)
        self.assertNotIn("AppData\\Local\\Tesseract-OCR", combined)
        self.assertIn("RECRUITOS_TESSERACT_CMD", combined)


if __name__ == "__main__":
    unittest.main()
