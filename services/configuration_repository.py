"""Key/value application configuration access."""
from __future__ import annotations

from typing import Any

from config.sheet_names import CONFIGURATION
from services.base_repository import BaseRepository
from services.master_repository import MasterRepository


class ConfigurationRepository(BaseRepository):
    def __init__(self) -> None:
        dataframe = MasterRepository.get_sheet(CONFIGURATION).copy().fillna("")
        if "Key" not in dataframe.columns or "Value" not in dataframe.columns:
            raise ValueError("Configuration sheet must contain Key and Value columns.")
        self._values: dict[str, Any] = {}
        for _, row in dataframe.iterrows():
            key = str(row.get("Key", "")).strip()
            if not key:
                continue
            normalized = self.normalize_text(key)
            if normalized in self._values:
                raise ValueError(f"Duplicate configuration key '{key}'.")
            self._values[normalized] = row.get("Value", "")

    def get(self, key: str, default: Any = None) -> Any:
        return self._values.get(self.normalize_text(key), default)

    def get_float(self, key: str, default: float | None = None) -> float | None:
        value = self.get(key, default)
        if value is None or str(value).strip() == "":
            return default
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Configuration '{key}' must be numeric.") from exc
