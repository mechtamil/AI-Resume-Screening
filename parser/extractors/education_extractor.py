"""Extract standardized education values using EducationRepository."""
from __future__ import annotations

import re

from services.education_repository import EducationRepository


class EducationExtractor:
    repository: EducationRepository | None = None

    SECTION_HEADERS = {
        "education",
        "educational qualification",
        "educational qualifications",
        "academic qualification",
        "academic qualifications",
        "qualification",
        "qualifications",
        "academics",
    }

    STOP_HEADERS = {
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "skills",
        "technical skills",
        "projects",
        "certifications",
        "certification",
        "summary",
        "profile",
        "professional summary",
        "achievements",
        "languages",
        "personal details",
    }

    @classmethod
    def _repo(cls) -> EducationRepository:
        if cls.repository is None:
            cls.repository = EducationRepository()
        return cls.repository

    @classmethod
    def _education_section(cls, text: str) -> str:
        lines = [line.strip() for line in (text or "").splitlines()]
        collected: list[str] = []
        in_section = False
        for line in lines:
            normalized = re.sub(r"\s*[:\-]\s*$", "", line).strip().casefold()
            if normalized in cls.SECTION_HEADERS:
                in_section = True
                continue
            if in_section and normalized in cls.STOP_HEADERS:
                break
            if in_section and line:
                collected.append(line)
        return "\n".join(collected)

    @staticmethod
    def _is_short_alias(value: str) -> bool:
        compact = re.sub(r"[^A-Za-z0-9]", "", value or "")
        return compact.isalpha() and len(compact) <= 3

    @classmethod
    def _contains_value(cls, text: str, value: str, education_section: str = "") -> bool:
        if not text or not value:
            return False
        escaped = re.escape(value.strip())
        if cls._is_short_alias(value):
            # Short aliases such as BE/ME must preserve configured case. This
            # prevents ordinary words like "be" or "me" from becoming degrees.
            pattern = re.compile(rf"(?<!\w){escaped}(?!\w)")
            return pattern.search(text) is not None
        pattern = re.compile(rf"(?<!\w){escaped}(?!\w)", re.I)
        return pattern.search(text) is not None or pattern.search(education_section) is not None

    @classmethod
    def extract(cls, text: str) -> list[str]:
        if not text:
            return []
        repo = cls._repo()
        section = cls._education_section(text)
        extracted: list[str] = []
        seen: set[str] = set()
        for degree in repo.get_all_degrees():
            values = [degree, *repo.get_aliases(degree)]
            if any(
                cls._contains_value(text, value, section)
                for value in sorted(values, key=len, reverse=True)
                if value
            ):
                standard = repo.normalize_degree(degree)
                if standard and standard.casefold() not in seen:
                    seen.add(standard.casefold())
                    extracted.append(standard)
        return extracted
