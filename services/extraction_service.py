"""
RecruitOS - Document Extraction Service

This service prepares raw text extracted from resumes and job descriptions
before it is passed to the parser.

Author: RecruitOS
"""

import re
from typing import Dict, List


class ExtractionService:
    """Service responsible for cleaning and preprocessing document text."""

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Removes unwanted whitespace and invisible characters.
        """

        if not text:
            return ""

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove tabs
        text = text.replace("\t", " ")

        # Remove multiple spaces
        text = re.sub(r"[ ]{2,}", " ", text)

        # Remove multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Standardizes spacing and formatting.
        """

        lines = []

        for line in text.split("\n"):

            line = line.strip()

            if line:
                lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def extract_sections(text: str) -> Dict[str, List[str]]:
        """
        Very basic section detector.

        This will be enhanced in future milestones.
        """

        section_headers = [
            "PROFILE",
            "SUMMARY",
            "EXPERIENCE",
            "WORK EXPERIENCE",
            "SKILLS",
            "TECHNICAL SKILLS",
            "PROJECTS",
            "EDUCATION",
            "CERTIFICATIONS",
            "ACHIEVEMENTS"
        ]

        current_section = "GENERAL"

        sections = {
            current_section: []
        }

        for line in text.split("\n"):

            cleaned = line.strip()

            upper = cleaned.upper()

            if upper in section_headers:

                current_section = upper

                sections[current_section] = []

                continue

            sections.setdefault(current_section, []).append(cleaned)

        return sections

    @staticmethod
    def calculate_metadata(text: str) -> Dict:
        """
        Returns document statistics.
        """

        words = text.split()

        lines = text.split("\n")

        paragraphs = [x for x in text.split("\n\n") if x.strip()]

        return {
            "character_count": len(text),
            "word_count": len(words),
            "line_count": len(lines),
            "paragraph_count": len(paragraphs)
        }

    @classmethod
    def preprocess_document(cls, text: str) -> Dict:
        """
        Complete preprocessing pipeline.
        """

        cleaned = cls.clean_text(text)

        normalized = cls.normalize_text(cleaned)

        sections = cls.extract_sections(normalized)

        metadata = cls.calculate_metadata(normalized)

        return {
            "text": normalized,
            "sections": sections,
            "metadata": metadata
        }