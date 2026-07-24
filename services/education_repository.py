"""Configuration-driven education repository."""
from __future__ import annotations

import re
from typing import Any

import pandas as pd

from config.sheet_names import EDUCATION
from services.base_repository import BaseRepository
from services.master_repository import MasterRepository


class EducationRepository(BaseRepository):
    SHEET_NAME = EDUCATION
    EDUCATION_COLUMN = "Education"
    ALIAS_COLUMN = "Alias"
    PRIORITY_COLUMN = "Priority"
    ACTIVE_COLUMN = "Active"

    def __init__(self) -> None:
        self._dataframe = pd.DataFrame()
        self._education_by_name: dict[str, dict[str, Any]] = {}
        self._alias_to_standard: dict[str, str] = {}
        self.load_repository()

    def load_repository(self) -> None:
        dataframe = MasterRepository.get_sheet(self.SHEET_NAME).copy().fillna("")
        if self.EDUCATION_COLUMN not in dataframe.columns:
            raise ValueError("Education sheet must contain an 'Education' column.")
        dataframe = self.filter_active(dataframe, self.ACTIVE_COLUMN).reset_index(drop=True)
        self._dataframe = dataframe
        self._build_indexes()

    @classmethod
    def _parse_aliases(cls, value: Any) -> list[str]:
        if value is None:
            return []
        seen: set[str] = set()
        output: list[str] = []
        for item in re.split(r"[;,|]", str(value)):
            item = item.strip()
            key = cls.normalize_text(item)
            if key and key not in seen:
                seen.add(key)
                output.append(item)
        return output

    @staticmethod
    def _parse_priority(value: Any) -> int | float | str | None:
        if value is None or str(value).strip() == "":
            return None
        if isinstance(value, bool):
            return str(value)
        try:
            number = float(value)
            return int(number) if number.is_integer() else number
        except (TypeError, ValueError):
            return str(value).strip()

    def _register_alias(self, alias: str, standard: str) -> None:
        key = self.normalize_text(alias)
        if not key:
            return
        existing = self._alias_to_standard.get(key)
        if existing and self.normalize_text(existing) != self.normalize_text(standard):
            raise ValueError(
                f"Ambiguous education alias '{alias}' maps to both '{existing}' and '{standard}'."
            )
        self._alias_to_standard[key] = standard

    def _build_indexes(self) -> None:
        self._education_by_name = {}
        self._alias_to_standard = {}
        for _, row in self._dataframe.iterrows():
            name = str(row.get(self.EDUCATION_COLUMN, "")).strip()
            if not name:
                continue
            key = self.normalize_text(name)
            if key in self._education_by_name:
                raise ValueError(f"Duplicate active education value '{name}'.")
            aliases = self._parse_aliases(row.get(self.ALIAS_COLUMN, ""))
            record = {"name": name, "aliases": aliases, "priority": self._parse_priority(row.get(self.PRIORITY_COLUMN, ""))}
            self._education_by_name[key] = record
            self._register_alias(name, name)
            for alias in aliases:
                self._register_alias(alias, name)

    def get_all_degrees(self) -> list[str]:
        return sorted((r["name"] for r in self._education_by_name.values()), key=str.lower)

    def get_degree_names(self) -> list[str]:
        return self.get_all_degrees()

    def total_degrees(self) -> int:
        return len(self._education_by_name)

    def find_standard_degree(self, value: str) -> str | None:
        return self._alias_to_standard.get(self.normalize_text(value)) if value else None

    def normalize_degree(self, value: str) -> str | None:
        return self.find_standard_degree(value)

    def is_valid_degree(self, value: str) -> bool:
        return self.find_standard_degree(value) is not None

    def get_degree_details(self, value: str) -> dict[str, Any] | None:
        standard = self.find_standard_degree(value)
        if not standard:
            return None
        record = self._education_by_name.get(self.normalize_text(standard))
        return dict(record) if record else None

    def get_aliases(self, value: str) -> list[str]:
        details = self.get_degree_details(value)
        return list(details["aliases"]) if details else []

    def get_priority(self, value: str) -> int | float | str | None:
        details = self.get_degree_details(value)
        return details["priority"] if details else None

    def search_degrees(self, query: str) -> list[dict[str, Any]]:
        target = self.normalize_text(query)
        if not target:
            return []
        results = []
        for record in self._education_by_name.values():
            values = [record["name"], *record["aliases"], str(record["priority"] or "")]
            if any(target in self.normalize_text(value) for value in values):
                results.append(dict(record))
        return sorted(results, key=lambda item: item["name"].lower())

    def get_dataframe(self) -> pd.DataFrame:
        return self._dataframe.copy()

    def refresh(self) -> None:
        MasterRepository.reload()
        self.load_repository()

    def display_summary(self) -> None:
        print("\nRecruitOS Enterprise Education Repository")
        print("-" * 60)
        print(f"Total Degrees : {self.total_degrees()}")
        print("-" * 60)
