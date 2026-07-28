"""Extract personal/contact information from resume text."""
from __future__ import annotations

import logging
import re
from typing import Dict, List

from parser.extractors.name_extractor import NameExtractor
from services.location_repository import LocationRepository

logger = logging.getLogger(__name__)


class PersonalExtractor:
    EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    PHONE_PATTERN = re.compile(r"(\+?\d[\d\s\-()]{8,18}\d)")
    LINKEDIN_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9_\-/.]+", re.I)
    GITHUB_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_\-/.]+", re.I)
    WEBSITE_PATTERN = re.compile(r"https?://[^\s<>]+", re.I)
    LOCATION_LABEL_PATTERN = re.compile(
        r"(?im)^\s*(?:location|current location|city|address)\s*[:\-]\s*([^\n|;,]{2,80})"
    )

    _location_repository: LocationRepository | None = None

    @classmethod
    def _get_location_repository(cls) -> LocationRepository | None:
        if cls._location_repository is not None:
            return cls._location_repository
        try:
            cls._location_repository = LocationRepository()
        except Exception:
            # Location master data is optional for personal extraction.
            logger.debug("Location repository unavailable", exc_info=True)
            return None
        return cls._location_repository

    @staticmethod
    def split_lines(text: str) -> List[str]:
        return [line.strip() for line in (text or "").splitlines() if line.strip()]

    @classmethod
    def extract_name(cls, lines: List[str]) -> str:
        return NameExtractor().extract("\n".join(lines)) if lines else ""

    @classmethod
    def extract_email(cls, text: str) -> str:
        match = cls.EMAIL_PATTERN.search(text or "")
        return match.group(0) if match else ""

    @classmethod
    def extract_phone(cls, text: str) -> str:
        match = cls.PHONE_PATTERN.search(text or "")
        return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""

    @classmethod
    def extract_location(cls, text: str) -> str:
        text = text or ""
        labelled = cls.LOCATION_LABEL_PATTERN.search(text)
        if labelled:
            return labelled.group(1).strip()

        repository = cls._get_location_repository()
        if repository:
            for value in repository.get_search_values():
                if re.search(rf"(?<!\w){re.escape(value)}(?!\w)", text, re.I):
                    return value
        return ""

    @classmethod
    def extract_linkedin(cls, text: str) -> str:
        match = cls.LINKEDIN_PATTERN.search(text or "")
        return match.group(0) if match else ""

    @classmethod
    def extract_github(cls, text: str) -> str:
        match = cls.GITHUB_PATTERN.search(text or "")
        return match.group(0) if match else ""

    @classmethod
    def extract_website(cls, text: str) -> str:
        for website in cls.WEBSITE_PATTERN.findall(text or ""):
            lowered = website.lower()
            if "linkedin.com" not in lowered and "github.com" not in lowered:
                return website.rstrip(".,;)")
        return ""

    @classmethod
    def extract(cls, text: str) -> Dict[str, str]:
        try:
            lines = cls.split_lines(text)
            return {
                "full_name": cls.extract_name(lines),
                "email": cls.extract_email(text),
                "phone": cls.extract_phone(text),
                "location": cls.extract_location(text),
                "linkedin": cls.extract_linkedin(text),
                "github": cls.extract_github(text),
                "website": cls.extract_website(text),
            }
        except Exception as exc:
            logger.exception("Personal extraction failed: %s", exc)
            return {
                "full_name": "",
                "email": "",
                "phone": "",
                "location": "",
                "linkedin": "",
                "github": "",
                "website": "",
            }
