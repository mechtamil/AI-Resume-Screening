"""Configuration-driven scoring weights repository."""
from __future__ import annotations

from typing import Any

import pandas as pd

from config.sheet_names import SCORING
from services.base_repository import BaseRepository
from services.master_repository import MasterRepository


class ScoringRepository(BaseRepository):
    SHEET_NAME = SCORING
    COMPONENT_COLUMN = "Component"
    WEIGHT_COLUMN = "Weight"
    ACTIVE_COLUMN = "Active"
    REMARKS_COLUMN = "Remarks"

    def __init__(self) -> None:
        self._dataframe = pd.DataFrame()
        self._components: dict[str, dict[str, Any]] = {}
        self.load_repository()

    def load_repository(self) -> None:
        dataframe = MasterRepository.get_sheet(self.SHEET_NAME).copy().fillna("")
        for column in (self.COMPONENT_COLUMN, self.WEIGHT_COLUMN):
            if column not in dataframe.columns:
                raise ValueError(f"Scoring sheet must contain '{column}'.")
        dataframe = self.filter_active(dataframe, self.ACTIVE_COLUMN).reset_index(drop=True)
        self._dataframe = dataframe
        self._build_index()

    @staticmethod
    def _parse_weight(value: Any, component: str) -> float:
        if value is None or isinstance(value, bool) or str(value).strip() == "":
            raise ValueError(f"Missing or invalid scoring weight for '{component}'.")
        try:
            weight = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Scoring weight for '{component}' must be numeric.") from exc
        if weight < 0:
            raise ValueError(f"Scoring weight for '{component}' cannot be negative.")
        return weight

    def _build_index(self) -> None:
        self._components = {}
        for _, row in self._dataframe.iterrows():
            component = str(row.get(self.COMPONENT_COLUMN, "")).strip()
            if not component:
                continue
            key = self.normalize_text(component)
            if key in self._components:
                raise ValueError(f"Duplicate active scoring component '{component}'.")
            self._components[key] = {
                "name": component,
                "weight": self._parse_weight(row.get(self.WEIGHT_COLUMN, ""), component),
                "remarks": str(row.get(self.REMARKS_COLUMN, "")).strip(),
            }

    def get_active_components(self) -> list[str]:
        return [record["name"] for record in self._components.values()]

    def get_components(self) -> list[str]:
        return self.get_active_components()

    def is_valid_component(self, component: str) -> bool:
        return self.normalize_text(component) in self._components

    def get_weight(self, component: str) -> float | None:
        record = self._components.get(self.normalize_text(component))
        return float(record["weight"]) if record else None

    def require_weight(self, component: str) -> float:
        weight = self.get_weight(component)
        if weight is None:
            raise KeyError(f"Scoring component not found or inactive: '{component}'.")
        return weight

    def get_all_weights(self) -> dict[str, float]:
        return {record["name"]: float(record["weight"]) for record in self._components.values()}

    def get_total_weight(self) -> float:
        return sum(self.get_all_weights().values())

    def validate_total_weight(self, expected_total: float) -> bool:
        try:
            expected = float(expected_total)
        except (TypeError, ValueError) as exc:
            raise ValueError("Expected scoring total must be numeric.") from exc
        return abs(self.get_total_weight() - expected) < 1e-9

    def get_remarks(self, component: str) -> str | None:
        details = self.get_component_details(component)
        return details["remarks"] if details else None

    def get_component_details(self, component: str) -> dict[str, Any] | None:
        record = self._components.get(self.normalize_text(component))
        return dict(record) if record else None

    def get_all_component_details(self) -> list[dict[str, Any]]:
        return [dict(record) for record in self._components.values()]

    def search_components(self, query: str) -> list[dict[str, Any]]:
        target = self.normalize_text(query)
        if not target:
            return []
        return [
            dict(record)
            for record in self._components.values()
            if target in self.normalize_text(record["name"])
            or target in self.normalize_text(record["remarks"])
        ]

    def get_dataframe(self) -> pd.DataFrame:
        return self._dataframe.copy()

    def refresh(self) -> None:
        MasterRepository.reload()
        self.load_repository()

    def total_components(self) -> int:
        return len(self._components)

    def display_summary(self) -> None:
        print("\nRecruitOS Enterprise Scoring Repository")
        print("-" * 60)
        print(f"Active Components : {self.total_components()}")
        print(f"Total Weight      : {self.get_total_weight()}")
        print("-" * 60)
