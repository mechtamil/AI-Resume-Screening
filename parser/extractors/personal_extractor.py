"""
============================================================
RecruitOS
Enterprise Personal Information Extractor
Version : 2.1
Author  : Tamilvanan A

Description:
Extracts candidate personal information from resume text.

This module is designed to be reusable across:

• Resume Parser
• Candidate Database
• AI Matching Engine
• ATS Search
• Interview Engine

============================================================
"""

import re
import logging
from typing import Dict, List


logger = logging.getLogger(__name__)


class PersonalExtractor:
    """
    Enterprise Personal Information Extractor
    """

    EMAIL_PATTERN = re.compile(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    )

    PHONE_PATTERN = re.compile(
        r"(\+?\d[\d\s\-\(\)]{8,18}\d)"
    )

    LINKEDIN_PATTERN = re.compile(
        r"(https?://)?(www\.)?linkedin\.com/in/[A-Za-z0-9_\-]+",
        re.IGNORECASE
    )

    GITHUB_PATTERN = re.compile(
        r"(https?://)?(www\.)?github\.com/[A-Za-z0-9_\-]+",
        re.IGNORECASE
    )

    WEBSITE_PATTERN = re.compile(
        r"(https?://[A-Za-z0-9./_-]+)",
        re.IGNORECASE
    )

    COMMON_LOCATIONS = [
        "Chennai",
        "Bangalore",
        "Bengaluru",
        "Hyderabad",
        "Pune",
        "Mumbai",
        "Delhi",
        "Noida",
        "Coimbatore",
        "Trichy",
        "Madurai",
        "India"
    ]

    @staticmethod
    def split_lines(text: str) -> List[str]:
        """
        Split text into cleaned lines.
        """

        if not text:
            return []

        return [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

    @classmethod
    def extract_name(cls, lines: List[str]) -> str:
        """
        Candidate name is assumed to be
        the first meaningful line.
        """

        if not lines:
            return ""

        return lines[0]

    @classmethod
    def extract_email(cls, text: str) -> str:

        match = cls.EMAIL_PATTERN.search(text)

        if match:
            return match.group()

        return ""

    @classmethod
    def extract_phone(cls, text: str) -> str:

        match = cls.PHONE_PATTERN.search(text)

        if match:
            return match.group().strip()

        return ""

    @classmethod
    def extract_location(cls, text: str) -> str:

        for city in cls.COMMON_LOCATIONS:

            pattern = r"\b" + re.escape(city) + r"\b"

            if re.search(pattern, text, re.IGNORECASE):
                return city

        return ""

    @classmethod
    def extract_linkedin(cls, text: str) -> str:

        match = cls.LINKEDIN_PATTERN.search(text)

        if match:
            return match.group()

        return ""

    @classmethod
    def extract_github(cls, text: str) -> str:

        match = cls.GITHUB_PATTERN.search(text)

        if match:
            return match.group()

        return ""

    @classmethod
    def extract_website(cls, text: str) -> str:

        websites = cls.WEBSITE_PATTERN.findall(text)

        for website in websites:

            if "linkedin" in website.lower():
                continue

            if "github" in website.lower():
                continue

            return website

        return ""

    @classmethod
    def extract(cls, text: str) -> Dict:
        """
        Main extraction method.

        Returns a dictionary that can be
        directly consumed by ResumeParser.
        """

        try:

            lines = cls.split_lines(text)

            return {

                "full_name": cls.extract_name(lines),

                "email": cls.extract_email(text),

                "phone": cls.extract_phone(text),

                "location": cls.extract_location(text),

                "linkedin": cls.extract_linkedin(text),

                "github": cls.extract_github(text),

                "website": cls.extract_website(text)

            }

        except Exception as ex:

            logger.exception(
                "Personal Extraction Failed : %s",
                ex
            )

            return {

                "full_name": "",

                "email": "",

                "phone": "",

                "location": "",

                "linkedin": "",

                "github": "",

                "website": ""

            }