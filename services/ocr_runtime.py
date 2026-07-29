"""Tesseract runtime discovery and pytesseract configuration.

No operating-system or user-specific path is stored in source code. Deployments may
provide ``RECRUITOS_TESSERACT_CMD`` or expose ``tesseract`` through ``PATH``.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any


def resolve_tesseract_command(configured_command: str | None = None) -> str | None:
    """Return a usable Tesseract command from deployment configuration or PATH.

    A configured value may be either an absolute/relative executable path or a command
    name resolvable through ``PATH``. Invalid configured values fail clearly instead
    of silently falling back to an unexpected executable.
    """
    raw_value = str(configured_command or "").strip()
    if raw_value:
        expanded = os.path.expandvars(os.path.expanduser(raw_value))
        candidate = Path(expanded)

        if candidate.is_file():
            return str(candidate.resolve())

        discovered = shutil.which(expanded)
        if discovered:
            return discovered

        raise RuntimeError(
            "The configured Tesseract executable was not found. "
            "Update RECRUITOS_TESSERACT_CMD or remove it to use PATH discovery."
        )

    return shutil.which("tesseract")


def configure_pytesseract(
    pytesseract_module: Any,
    configured_command: str | None = None,
) -> str:
    """Configure a pytesseract module and return the resolved executable command."""
    command = resolve_tesseract_command(configured_command)
    if not command:
        raise RuntimeError(
            "Image OCR requires the Tesseract runtime. Install it and expose "
            "'tesseract' on PATH, or configure RECRUITOS_TESSERACT_CMD."
        )

    pytesseract_module.pytesseract.tesseract_cmd = command
    return command
