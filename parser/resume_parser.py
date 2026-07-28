"""Transform processed resume documents into Candidate domain objects."""
from __future__ import annotations

import re
from typing import Any

from models.candidate import Candidate
from parser.extractors.certification_extractor import CertificationExtractor
from parser.extractors.education_extractor import EducationExtractor
from parser.extractors.personal_extractor import PersonalExtractor
from parser.extractors.skill_extractor import SkillExtractor


class ResumeParser:
    EXPERIENCE_PATTERNS = (
        re.compile(
            r"(?:total\s+)?(?:professional\s+)?experience\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)",
            re.I,
        ),
        re.compile(r"(?<!\d)(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)(?:\s+of\s+(?:\w+\s+){0,3})?experience", re.I),
    )

    @staticmethod
    def remove_duplicates(values: list[str]) -> list[str]:
        output: list[str] = []
        seen: set[str] = set()
        for value in values or []:
            cleaned = str(value or "").strip()
            key = cleaned.casefold()
            if cleaned and key not in seen:
                seen.add(key)
                output.append(cleaned)
        return output

    @classmethod
    def extract_experience(cls, text: str) -> float:
        """Extract explicitly stated total experience; do not infer employment timelines."""
        if not text:
            return 0.0
        values: list[float] = []
        for pattern in cls.EXPERIENCE_PATTERNS:
            for match in pattern.findall(text):
                try:
                    values.append(float(match))
                except (TypeError, ValueError):
                    pass
        return max(values) if values else 0.0

    @classmethod
    def extract_skills(cls, text: str) -> list[str]:
        return cls.remove_duplicates(SkillExtractor.extract(text)) if text else []

    @classmethod
    def extract_education(cls, text: str) -> list[str]:
        return cls.remove_duplicates(EducationExtractor.extract(text)) if text else []

    @classmethod
    def extract_certifications(cls, text: str) -> list[str]:
        return cls.remove_duplicates(CertificationExtractor.extract(text)) if text else []

    @staticmethod
    def extract_tools(text: str) -> list[str]:
        return []

    @staticmethod
    def extract_projects(text: str) -> list[str]:
        return []

    @staticmethod
    def extract_companies(text: str) -> list[str]:
        return []

    @staticmethod
    def extract_soft_skills(text: str) -> list[str]:
        return []

    @classmethod
    def parse(cls, document: dict[str, Any] | None) -> Candidate:
        candidate = Candidate()
        if not document:
            return candidate

        candidate.source_file = str(document.get("file_name", "") or "").strip()
        text = str(document.get("text", "") or "").strip()
        candidate.raw_text = text
        if not text:
            return candidate

        personal = PersonalExtractor.extract(text) or {}
        candidate.full_name = str(personal.get("full_name", "") or "").strip()
        candidate.email = str(personal.get("email", "") or "").strip()
        candidate.phone = str(personal.get("phone", "") or "").strip()
        candidate.location = str(personal.get("location", "") or "").strip()
        candidate.linkedin = str(personal.get("linkedin", "") or "").strip()
        candidate.github = str(personal.get("github", "") or "").strip()
        candidate.website = str(personal.get("website", "") or "").strip()

        candidate.total_experience = cls.extract_experience(text)
        candidate.education = cls.extract_education(text)
        candidate.certifications = cls.extract_certifications(text)
        candidate.technical_skills = cls.extract_skills(text)
        candidate.soft_skills = cls.extract_soft_skills(text)
        candidate.tools = cls.extract_tools(text)
        candidate.projects = cls.extract_projects(text)
        candidate.companies = cls.extract_companies(text)
        return candidate
