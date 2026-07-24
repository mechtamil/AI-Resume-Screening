"""Heuristic candidate-name extractor."""
from __future__ import annotations

import re


class NameExtractor:
    SECTION_TERMS = {
        "resume", "curriculum vitae", "profile", "professional summary", "career objective",
        "objective", "technical skills", "education", "educational qualifications", "experience",
        "work experience", "projects", "skills", "contact", "personal details", "summary",
        "certifications", "achievements",
    }
    CONTACT_TERMS = ("email", "mobile", "phone", "address", "linkedin", "github", "www.", "http")

    @classmethod
    def extract(cls, text: str) -> str:
        if not text:
            return ""
        lines = [line.strip() for line in text.splitlines() if line.strip()][:15]
        for line in lines:
            lowered = line.casefold().strip(" :-")
            if lowered in cls.SECTION_TERMS:
                continue
            if any(term in lowered for term in cls.CONTACT_TERMS) or "@" in line:
                continue
            if sum(ch.isdigit() for ch in line) >= 4:
                continue

            cleaned = re.sub(r"[^A-Za-z .'-]", " ", line)
            cleaned = re.sub(r"\s+", " ", cleaned).strip(" .'-")
            words = [word for word in cleaned.split() if word]
            if not 2 <= len(words) <= 5:
                continue

            # Allow one-letter initials, but not multiple isolated letters that
            # are typical of letter-spaced section headings.
            one_letter_count = sum(len(re.sub(r"[^A-Za-z]", "", word)) == 1 for word in words)
            if one_letter_count > 1:
                continue
            if any(len(re.sub(r"[^A-Za-z]", "", word)) == 0 for word in words):
                continue

            return cleaned
        return ""
