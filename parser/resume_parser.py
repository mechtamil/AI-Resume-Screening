"""
============================================================
RecruitOS
Resume Parser
Version : 1.0
Author  : Tamilvanan A

Description:
Parses a processed resume document into a Candidate model.
============================================================
"""

import re

from models.candidate import Candidate


class ResumeParser:

    EMAIL_PATTERN = re.compile(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    )

    PHONE_PATTERN = re.compile(
        r"(\+?\d[\d\s\-]{8,15}\d)"
    )

    EXPERIENCE_PATTERN = re.compile(
        r"(\d+(?:\.\d+)?)\s*(?:\+)?\s*(?:years|yrs|year)",
        re.IGNORECASE
    )

    @classmethod
    def parse(cls, document: dict) -> Candidate:

        candidate = Candidate()

        candidate.source_file = document.get("file_name", "")

        candidate.raw_text = document.get("text", "")

        text = candidate.raw_text

        lines = [
            line.strip()
            for line in text.split("\n")
            if line.strip()
        ]

        # Candidate Name
        if lines:
            candidate.full_name = lines[0]

        # Email
        email = cls.EMAIL_PATTERN.search(text)

        if email:
            candidate.email = email.group()

        # Phone
        phone = cls.PHONE_PATTERN.search(text)

        if phone:
            candidate.phone = phone.group().strip()

        # Experience
        exp = cls.EXPERIENCE_PATTERN.search(text)

        if exp:
            candidate.total_experience = float(exp.group(1))

        return candidate