"""
============================================================
RecruitOS
Phone Extractor
Version : 0.5
Author  : Tamilvanan A
============================================================
"""

import re


class PhoneExtractor:
    """
    Extract phone number from resume text.
    """

    PHONE_PATTERN = re.compile(
        r'(?:\+91[\s\-]?)?(?:\(?0?\)?[\s\-]?)?([6-9]\d{9})'
    )

    def extract(self, text: str) -> dict:

        if not text:
            return {
                "value": "",
                "confidence": 0.0
            }

        matches = self.PHONE_PATTERN.findall(text)

        if not matches:
            return {
                "value": "",
                "confidence": 0.0
            }

        phone = matches[0]

        return {
            "value": phone,
            "confidence": 0.98
        }