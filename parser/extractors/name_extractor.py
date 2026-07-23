"""
============================================================
RecruitOS
Name Extractor
Version : 0.5
Author  : Tamilvanan A
============================================================
"""

import re


class NameExtractor:
    """
    Extract candidate name from resume text.
    """

    def __init__(self):
        pass

    def extract(self, text: str) -> str:

        if not text:
            return ""

        lines = text.split("\n")

        cleaned = []

        for line in lines:

            line = line.strip()

            if len(line) < 3:
                continue

            cleaned.append(line)

        # Common labels
        ignore = [
            "resume",
            "curriculum vitae",
            "profile",
            "professional summary",
            "career objective",
            "technical skills",
            "education",
            "experience",
            "projects",
            "skills",
            "contact"
        ]

        for line in cleaned[:12]:

            lower = line.lower()

            if any(word in lower for word in ignore):
                continue

            # remove symbols
            temp = re.sub(r"[^A-Za-z\s]", "", line)

            words = temp.split()

            if len(words) < 2:
                continue

            if len(words) > 4:
                continue

            valid = True

            for w in words:

                if len(w) < 2:
                    valid = False

            if valid:
                return " ".join(words)

        return ""