"""
============================================================
RecruitOS

Module      : Education Extractor
Sprint      : 5.6.0
Version     : 1.0.0
Author      : Tamilvanan A

Purpose:
Extracts standardized education qualifications from resume
text using EducationRepository.

Important:
- No education values are hardcoded.
- All degrees and aliases come from:
  RecruitOS_Configuration.xlsx -> Education sheet.

============================================================
"""

from __future__ import annotations

import re
from typing import List

from services.education_repository import EducationRepository


class EducationExtractor:
    """
    Configuration-driven Education Extractor.

    Detects both:

        - Standard education names
        - Configured aliases

    Every match is returned using the standardized education
    name defined in RecruitOS_Configuration.xlsx.
    """

    repository = EducationRepository()

    # ========================================================
    # Pattern Builder
    # ========================================================

    @staticmethod
    def _build_pattern(
        value: str
    ) -> re.Pattern:
        """
        Build a safe case-insensitive search pattern.

        Lookarounds prevent short aliases from matching inside
        unrelated larger words.

        Example:

            Alias: BE

        should not match:

            "member"
        """

        escaped_value = re.escape(
            value.strip()
        )

        return re.compile(
            rf"(?<!\w){escaped_value}(?!\w)",
            re.IGNORECASE
        )

    # ========================================================
    # Match Text
    # ========================================================

    @classmethod
    def _contains_value(
        cls,
        text: str,
        value: str
    ) -> bool:
        """
        Check whether a configured education value occurs in
        the resume text.
        """

        if not text or not value:

            return False

        pattern = cls._build_pattern(
            value
        )

        return (
            pattern.search(text)
            is not None
        )

    # ========================================================
    # Extract Education
    # ========================================================

    @classmethod
    def extract(
        cls,
        text: str
    ) -> List[str]:
        """
        Extract standardized education qualifications.

        Workflow:

            Resume Text
                ↓
        Standard Degree + Aliases
                ↓
        EducationRepository
                ↓
        Standardized Education List

        Duplicate qualifications are removed.
        """

        if not text:

            return []

        extracted = []

        seen = set()

        for degree in (
            cls.repository.get_all_degrees()
        ):

            search_values = [
                degree
            ]

            search_values.extend(
                cls.repository.get_aliases(
                    degree
                )
            )

            # Longer strings first.
            #
            # This improves deterministic matching when both
            # a full name and shorter alias are configured.

            search_values = sorted(
                search_values,
                key=len,
                reverse=True
            )

            matched = any(

                cls._contains_value(
                    text,
                    value
                )

                for value
                in search_values

                if value

            )

            if not matched:

                continue

            standard_degree = (
                cls.repository.normalize_degree(
                    degree
                )
            )

            if not standard_degree:

                continue

            normalized_standard = (
                standard_degree
                .strip()
                .lower()
            )

            if (
                normalized_standard
                not in seen
            ):

                seen.add(
                    normalized_standard
                )

                extracted.append(
                    standard_degree
                )

        return extracted


if __name__ == "__main__":

    sample_text = """
    Sample resume text.
    """

    print(
        EducationExtractor.extract(
            sample_text
        )
    )