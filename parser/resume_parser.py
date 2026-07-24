"""
============================================================
RecruitOS
Enterprise Resume Parser
Version : 2.1
Author  : Tamilvanan A

Description:
Coordinates all resume extractors and converts a
processed document into a structured Candidate object.

Architecture:

Document
      │
      ▼
ResumeParser
      │
      ├── PersonalExtractor
      ├── SkillsExtractor
      ├── EducationExtractor
      ├── ExperienceExtractor
      ├── ProjectExtractor
      └── CertificationExtractor

Returns:
    Candidate
============================================================
"""

import re

from models.candidate import Candidate

from parser.extractors.personal_extractor import (
    PersonalExtractor
)


class ResumeParser:
    """
    Enterprise Resume Parser

    This class orchestrates all extractors.
    """

    EXPERIENCE_PATTERN = re.compile(
        r"(\d+(?:\.\d+)?)\s*(?:\+)?\s*(?:years|yrs|year)",
        re.IGNORECASE
    )

    # -------------------------------------------------------
    # Existing Helper Methods
    # (These will move into dedicated extractors in
    # future milestones.)
    # -------------------------------------------------------

    @staticmethod
    def remove_duplicates(items):

        unique = []

        for item in items:

            if item not in unique:
                unique.append(item)

        return unique

    @classmethod
    def extract_experience(cls, text):

        match = cls.EXPERIENCE_PATTERN.search(text)

        if match:

            try:

                return float(match.group(1))

            except ValueError:

                return 0.0

        return 0.0

    @classmethod
    def extract_skills(cls, text):

        # Sprint 5.3.3
        return []

    @classmethod
    def extract_tools(cls, text):

        # Sprint 5.3.3
        return []

    @classmethod
    def extract_education(cls, text):

        # Sprint 5.3.4
        return []

    @classmethod
    def extract_certifications(cls, text):

        # Sprint 5.3.6
        return []

    @classmethod
    def extract_projects(cls, lines):

        # Sprint 5.3.6
        return []

    # -------------------------------------------------------
    # Main Parser
    # -------------------------------------------------------

    @classmethod
    def parse(cls, document: dict) -> Candidate:
        """
        Parse resume document into Candidate.
        """

        candidate = Candidate()

        if document is None:

            return candidate

        candidate.source_file = document.get(
            "file_name",
            ""
        )

        candidate.raw_text = document.get(
            "text",
            ""
        )

        text = candidate.raw_text

        if not text:

            return candidate

        # ---------------------------------------------
        # Personal Information
        # ---------------------------------------------

        personal = PersonalExtractor.extract(
            text
        )

        candidate.full_name = personal["full_name"]

        candidate.email = personal["email"]

        candidate.phone = personal["phone"]

        candidate.location = personal["location"]

        # ---------------------------------------------
        # Experience
        # ---------------------------------------------

        candidate.total_experience = (
            cls.extract_experience(text)
        )

        # ---------------------------------------------
        # Education
        # ---------------------------------------------

        candidate.education = (
            cls.extract_education(text)
        )

        # ---------------------------------------------
        # Certifications
        # ---------------------------------------------

        candidate.certifications = (
            cls.extract_certifications(text)
        )

        # ---------------------------------------------
        # Technical Skills
        # ---------------------------------------------

        candidate.technical_skills = (
            cls.extract_skills(text)
        )

        # ---------------------------------------------
        # Tools
        # ---------------------------------------------

        candidate.tools = (
            cls.extract_tools(text)
        )

        # ---------------------------------------------
        # Projects
        # ---------------------------------------------

        lines = PersonalExtractor.split_lines(
            text
        )

        candidate.projects = (
            cls.extract_projects(lines)
        )

        return candidate