"""Document text cleaning, section detection, and metadata extraction."""
from __future__ import annotations

import re
from typing import Dict, List


class ExtractionService:
    SECTION_HEADERS = {
        "PROFILE", "SUMMARY", "PROFESSIONAL SUMMARY", "EXPERIENCE", "WORK EXPERIENCE",
        "PROFESSIONAL EXPERIENCE", "SKILLS", "TECHNICAL SKILLS", "PROJECTS", "EDUCATION",
        "CERTIFICATIONS", "ACHIEVEMENTS", "RESPONSIBILITIES", "MANDATORY SKILLS",
        "PREFERRED SKILLS", "KEYWORDS",
    }

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
        text = re.sub(r"[ \u00A0]{2,}", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def normalize_text(text: str) -> str:
        return "\n".join(line.strip() for line in (text or "").splitlines())

    @classmethod
    def extract_sections(cls, text: str) -> Dict[str, List[str]]:
        sections: Dict[str, List[str]] = {"GENERAL": []}
        current = "GENERAL"
        for line in (text or "").splitlines():
            cleaned = line.strip()
            normalized = re.sub(r"\s*[:\-]\s*$", "", cleaned).upper()
            if normalized in cls.SECTION_HEADERS:
                current = normalized
                sections.setdefault(current, [])
                continue
            sections.setdefault(current, []).append(cleaned)
        return sections

    @staticmethod
    def calculate_metadata(text: str) -> Dict[str, int]:
        text = text or ""
        return {
            "character_count": len(text),
            "word_count": len(text.split()),
            "line_count": len(text.splitlines()),
            "paragraph_count": len([p for p in re.split(r"\n\s*\n", text) if p.strip()]),
        }

    @classmethod
    def preprocess_document(cls, text: str) -> Dict:
        cleaned = cls.clean_text(text)
        normalized = cls.normalize_text(cleaned)
        return {
            "text": cleaned,
            "normalized_text": normalized,
            "sections": cls.extract_sections(normalized),
            "metadata": cls.calculate_metadata(cleaned),
        }
