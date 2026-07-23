"""
============================================================
RecruitOS
Email Extractor
Version : 0.5
Author  : Tamilvanan A
============================================================
"""

import re


class EmailExtractor:
    """
    Extract email address from resume text.
    """

    EMAIL_PATTERN = re.compile(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    )

    def extract(self, text: str) -> dict:
        """
        Returns:
        {
            "value": str,
            "confidence": float
        }
        """

        if not text:
            return {
                "value": "",
                "confidence": 0.0
            }

        matches = self.EMAIL_PATTERN.findall(text)

        if not matches:
            return {
                "value": "",
                "confidence": 0.0
            }

        return {
            "value": matches[0].lower(),
            "confidence": 0.99
        }