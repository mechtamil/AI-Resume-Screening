"""Extract standardized certifications using CertificationRepository.

Certification matching is intentionally context-aware. Aliases are not scanned
across the entire resume because names such as CATIA or Scrum may describe skills
rather than credentials.
"""
from __future__ import annotations

import re

from services.certification_repository import CertificationRepository


class CertificationExtractor:
    repository: CertificationRepository | None = None
    SECTION_HEADERS = {
        "certification", "certifications", "professional certifications", "credentials",
        "licenses and certifications", "certificates", "courses and certifications",
    }
    STOP_HEADERS = {
        "education", "experience", "work experience", "professional experience", "skills",
        "technical skills", "projects", "achievements", "summary", "profile", "languages",
        "personal details", "interests",
    }

    @classmethod
    def _repo(cls) -> CertificationRepository:
        if cls.repository is None:
            cls.repository = CertificationRepository()
        return cls.repository

    @classmethod
    def _search_context(cls, text: str) -> str:
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
        if collected:
            return "\n".join(collected)

        # Without a dedicated section, only inspect credential-context lines.
        contextual = [
            line
            for line in lines
            if re.search(r"\b(?:certif(?:ied|ication|ications)?|credential|licen[cs]e)\b", line, re.I)
        ]
        return "\n".join(contextual)

    @staticmethod
    def _is_short_alias(value: str) -> bool:
        compact = re.sub(r"[^A-Za-z0-9]", "", value or "")
        return compact.isalpha() and len(compact) <= 3

    @classmethod
    def _contains_value(cls, text: str, value: str) -> bool:
        if not text or not value:
            return False
        flags = 0 if cls._is_short_alias(value) else re.I
        return re.search(rf"(?<!\w){re.escape(value.strip())}(?!\w)", text, flags) is not None

    @classmethod
    def extract(cls, text: str) -> list[str]:
        context = cls._search_context(text)
        if not context:
            return []
        repo = cls._repo()
        extracted: list[str] = []
        seen: set[str] = set()
        for certification in repo.get_all_certifications():
            values = [certification, *repo.get_aliases(certification)]
            if any(
                cls._contains_value(context, value)
                for value in sorted(values, key=len, reverse=True)
                if value
            ):
                standard = repo.normalize_certification(certification)
                if standard and standard.casefold() not in seen:
                    seen.add(standard.casefold())
                    extracted.append(standard)
        return extracted
