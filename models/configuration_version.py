"""Immutable configuration selections used by RecruitOS screening runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ConfigurationSelection:
    """Resolved workbook and metadata for one configuration execution context."""

    tenant_id: int
    workbook_path: Path
    source: str = "system_default"
    version_id: int | None = None
    version_number: int | None = None
    configuration_key: str = "system-default"
    sha256: str = ""
    file_size: int = 0
    activated_at: str = ""
    sheet_summary: dict[str, dict[str, int]] = field(default_factory=dict)

    def require_valid(self) -> None:
        path = Path(self.workbook_path)
        if not path.is_file():
            raise FileNotFoundError(f"Configuration workbook not found: {path}")
        if self.tenant_id < 0:
            raise ValueError("Configuration tenant_id cannot be negative.")
        if not str(self.source or "").strip():
            raise ValueError("Configuration source is required.")
        if not str(self.configuration_key or "").strip():
            raise ValueError("Configuration key is required.")

    def summary(self) -> dict[str, Any]:
        """Return persistence-safe metadata without exposing local absolute paths."""
        return {
            "tenant_id": self.tenant_id,
            "source": self.source,
            "version_id": self.version_id,
            "version_number": self.version_number,
            "configuration_key": self.configuration_key,
            "sha256": self.sha256,
            "file_size": self.file_size,
            "activated_at": self.activated_at,
            "sheet_summary": dict(self.sheet_summary),
        }
