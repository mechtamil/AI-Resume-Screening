"""Configuration-driven certification repository."""
from __future__ import annotations

import re
from typing import Any

import pandas as pd

from config.sheet_names import CERTIFICATIONS
from services.base_repository import BaseRepository
from services.master_repository import MasterRepository


class CertificationRepository(BaseRepository):
    SHEET_NAME = CERTIFICATIONS
    CERTIFICATION_COLUMN = "Certification"
    ALIAS_COLUMN = "Alias"
    CATEGORY_COLUMN = "Category"
    ACTIVE_COLUMN = "Active"

    def __init__(self) -> None:
        self._dataframe = pd.DataFrame()
        self._certifications_by_name: dict[str, dict[str, Any]] = {}
        self._alias_to_standard: dict[str, str] = {}
        self.load_repository()

    def load_repository(self) -> None:
        dataframe = MasterRepository.get_sheet(self.SHEET_NAME).copy().fillna("")
        if self.CERTIFICATION_COLUMN not in dataframe.columns:
            raise ValueError("Certifications sheet must contain a 'Certification' column.")
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

    def _register_alias(self, alias: str, standard: str) -> None:
        key = self.normalize_text(alias)
        if not key:
            return
        existing = self._alias_to_standard.get(key)
        if existing and self.normalize_text(existing) != self.normalize_text(standard):
            raise ValueError(
                f"Ambiguous certification alias '{alias}' maps to both '{existing}' and '{standard}'."
            )
        self._alias_to_standard[key] = standard

    def _build_indexes(self) -> None:
        self._certifications_by_name = {}
        self._alias_to_standard = {}
        for _, row in self._dataframe.iterrows():
            name = str(row.get(self.CERTIFICATION_COLUMN, "")).strip()
            if not name:
                continue
            key = self.normalize_text(name)
            if key in self._certifications_by_name:
                raise ValueError(f"Duplicate active certification '{name}'.")
            aliases = self._parse_aliases(row.get(self.ALIAS_COLUMN, ""))
            record = {
                "name": name,
                "aliases": aliases,
                "category": str(row.get(self.CATEGORY_COLUMN, "")).strip(),
            }
            self._certifications_by_name[key] = record
            self._register_alias(name, name)
            for alias in aliases:
                self._register_alias(alias, name)

    def get_all_certifications(self) -> list[str]:
        return sorted((r["name"] for r in self._certifications_by_name.values()), key=str.lower)

    def get_all(self) -> list[str]:
        return self.get_all_certifications()

    def get_certification_names(self) -> list[str]:
        return self.get_all_certifications()

    def total_certifications(self) -> int:
        return len(self._certifications_by_name)

    def find_standard_certification(self, value: str) -> str | None:
        return self._alias_to_standard.get(self.normalize_text(value)) if value else None

    def get_standard_name(self, value: str) -> str | None:
        return self.find_standard_certification(value)

    def normalize_certification(self, value: str) -> str | None:
        return self.find_standard_certification(value)

    def normalize(self, value: str) -> str | None:
        return self.find_standard_certification(value)

    def is_valid_certification(self, value: str) -> bool:
        return self.find_standard_certification(value) is not None

    def is_valid(self, value: str) -> bool:
        return self.is_valid_certification(value)

    def find_alias(self, value: str) -> str | None:
        return self.find_standard_certification(value)

    def get_certification_details(self, value: str) -> dict[str, Any] | None:
        standard = self.find_standard_certification(value)
        if not standard:
            return None
        record = self._certifications_by_name.get(self.normalize_text(standard))
        return dict(record) if record else None

    def get_aliases(self, value: str) -> list[str]:
        details = self.get_certification_details(value)
        return list(details["aliases"]) if details else []

    def get_category(self, value: str) -> str | None:
        details = self.get_certification_details(value)
        return details["category"] if details else None

    def get_categories(self) -> list[str]:
        return sorted({r["category"] for r in self._certifications_by_name.values() if r["category"]}, key=str.lower)

    def get_certifications_by_category(self, category: str) -> list[str]:
        target = self.normalize_text(category)
        return sorted(
            [r["name"] for r in self._certifications_by_name.values() if self.normalize_text(r["category"]) == target],
            key=str.lower,
        )

    def search_certifications(self, query: str) -> list[dict[str, Any]]:
        target = self.normalize_text(query)
        if not target:
            return []
        results = []
        for record in self._certifications_by_name.values():
            values = [record["name"], record["category"], *record["aliases"]]
            if any(target in self.normalize_text(value) for value in values):
                results.append(dict(record))
        return sorted(results, key=lambda item: item["name"].lower())

    def get_dataframe(self) -> pd.DataFrame:
        return self._dataframe.copy()

    def refresh(self) -> None:
        MasterRepository.reload()
        self.load_repository()

    def display_summary(self) -> None:
        print("\nRecruitOS Enterprise Certification Repository")
        print("-" * 60)
        print(f"Total Certifications : {self.total_certifications()}")
        print(f"Total Categories      : {len(self.get_categories())}")
        print("-" * 60)
