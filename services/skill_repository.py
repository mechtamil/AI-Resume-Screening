"""Configuration-driven skill repository."""
from __future__ import annotations

import re
from typing import Any

import pandas as pd

from config.sheet_names import SKILLS
from services.base_repository import BaseRepository
from services.master_repository import MasterRepository


class SkillRepository(BaseRepository):
    SHEET_NAME = SKILLS
    SKILL_COLUMN = "Skill"
    CATEGORY_COLUMN = "Category"
    SUB_CATEGORY_COLUMN = "Sub Category"
    SYNONYMS_COLUMN = "Synonyms"
    ACTIVE_COLUMN = "Active"

    def __init__(self) -> None:
        self._dataframe = pd.DataFrame()
        self._skills_by_name: dict[str, dict[str, Any]] = {}
        self._alias_to_standard: dict[str, str] = {}
        self.load_repository()

    def load_repository(self) -> None:
        dataframe = MasterRepository.get_sheet(self.SHEET_NAME).copy().fillna("")
        if self.SKILL_COLUMN not in dataframe.columns:
            raise ValueError("Skills sheet must contain a 'Skill' column.")
        dataframe = self.filter_active(dataframe, self.ACTIVE_COLUMN).reset_index(drop=True)
        self._dataframe = dataframe
        self._build_indexes()

    @classmethod
    def _parse_synonyms(cls, value: Any) -> list[str]:
        if value is None:
            return []
        seen: set[str] = set()
        output: list[str] = []
        for item in re.split(r"[;,|]", str(value)):
            item = item.strip()
            normalized = cls.normalize_text(item)
            if normalized and normalized not in seen:
                seen.add(normalized)
                output.append(item)
        return output

    def _register_alias(self, alias: str, standard_name: str) -> None:
        normalized = self.normalize_text(alias)
        if not normalized:
            return
        existing = self._alias_to_standard.get(normalized)
        if existing and self.normalize_text(existing) != self.normalize_text(standard_name):
            raise ValueError(
                f"Ambiguous skill alias '{alias}' maps to both '{existing}' and "
                f"'{standard_name}'. Correct the Skills sheet."
            )
        self._alias_to_standard[normalized] = standard_name

    def _build_indexes(self) -> None:
        self._skills_by_name = {}
        self._alias_to_standard = {}
        for _, row in self._dataframe.iterrows():
            name = str(row.get(self.SKILL_COLUMN, "")).strip()
            if not name:
                continue
            key = self.normalize_text(name)
            if key in self._skills_by_name:
                raise ValueError(f"Duplicate active skill '{name}' in Skills sheet.")
            record = {
                "name": name,
                "category": str(row.get(self.CATEGORY_COLUMN, "")).strip(),
                "sub_category": str(row.get(self.SUB_CATEGORY_COLUMN, "")).strip(),
                "synonyms": self._parse_synonyms(row.get(self.SYNONYMS_COLUMN, "")),
            }
            self._skills_by_name[key] = record
            self._register_alias(name, name)
            for synonym in record["synonyms"]:
                self._register_alias(synonym, name)

    def get_all_skills(self) -> list[str]:
        return sorted((r["name"] for r in self._skills_by_name.values()), key=str.lower)

    def get_skill_names(self) -> list[str]:
        return self.get_all_skills()

    def total_skills(self) -> int:
        return len(self._skills_by_name)

    def find_standard_skill(self, value: str) -> str | None:
        return self._alias_to_standard.get(self.normalize_text(value)) if value else None

    def normalize_skill(self, value: str) -> str | None:
        return self.find_standard_skill(value)

    def is_valid_skill(self, skill: str) -> bool:
        return self.find_standard_skill(skill) is not None

    def get_skill_synonyms(self, skill: str) -> list[str]:
        details = self.get_skill_details(skill)
        return list(details["synonyms"]) if details else []

    def get_category(self, skill: str) -> str | None:
        details = self.get_skill_details(skill)
        return details["category"] if details else None

    def get_sub_category(self, skill: str) -> str | None:
        details = self.get_skill_details(skill)
        return details["sub_category"] if details else None

    def get_skill_details(self, skill: str) -> dict[str, Any] | None:
        standard = self.find_standard_skill(skill)
        if not standard:
            return None
        record = self._skills_by_name.get(self.normalize_text(standard))
        return dict(record) if record else None

    def get_skill_categories(self) -> list[str]:
        categories = {r["category"] for r in self._skills_by_name.values() if r["category"]}
        return sorted(categories, key=str.lower)

    def get_skills_by_category(self, category: str) -> list[str]:
        target = self.normalize_text(category)
        return sorted(
            [r["name"] for r in self._skills_by_name.values() if self.normalize_text(r["category"]) == target],
            key=str.lower,
        )

    def search_skills(self, query: str) -> list[dict[str, Any]]:
        target = self.normalize_text(query)
        if not target:
            return []
        results = []
        for record in self._skills_by_name.values():
            values = [record["name"], record["category"], record["sub_category"], *record["synonyms"]]
            if any(target in self.normalize_text(value) for value in values):
                results.append(dict(record))
        return sorted(results, key=lambda item: item["name"].lower())

    def get_dataframe(self) -> pd.DataFrame:
        return self._dataframe.copy()

    def refresh(self) -> None:
        MasterRepository.reload()
        self.load_repository()

    def display_summary(self) -> None:
        print("\nRecruitOS Enterprise Skill Repository")
        print("-" * 60)
        print(f"Total Skills     : {self.total_skills()}")
        print(f"Total Categories : {len(self.get_skill_categories())}")
        print("-" * 60)
