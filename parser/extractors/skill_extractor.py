"""Extract configured skills and aliases from free text."""
from __future__ import annotations

import re

from services.skill_repository import SkillRepository


class SkillExtractor:
    repository: SkillRepository | None = None

    @classmethod
    def _repo(cls) -> SkillRepository:
        if cls.repository is None:
            cls.repository = SkillRepository()
        return cls.repository

    @staticmethod
    def _contains(text: str, value: str) -> bool:
        if not text or not value:
            return False
        return re.search(rf"(?<!\w){re.escape(value.strip())}(?!\w)", text, re.I) is not None

    @classmethod
    def extract(cls, text: str) -> list[str]:
        if not text:
            return []
        repo = cls._repo()
        found: list[str] = []
        seen: set[str] = set()
        for standard in repo.get_all_skills():
            values = [standard, *repo.get_skill_synonyms(standard)]
            if any(cls._contains(text, value) for value in sorted(values, key=len, reverse=True)):
                key = standard.casefold()
                if key not in seen:
                    seen.add(key)
                    found.append(standard)
        return found

    @classmethod
    def contains_skill(cls, text: str, skill: str) -> bool:
        standard = cls._repo().find_standard_skill(skill)
        if not standard:
            return False
        values = [standard, *cls._repo().get_skill_synonyms(standard)]
        return any(cls._contains(text, value) for value in values)

    @classmethod
    def total_skills(cls) -> int:
        return cls._repo().total_skills()
