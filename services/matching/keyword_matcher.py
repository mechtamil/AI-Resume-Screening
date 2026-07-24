"""Keyword matching against candidate resume text."""
from __future__ import annotations

import re

from JD.jd_model import JobDescription
from models.candidate import Candidate
from models.match_result import MatchResult


class KeywordMatcher:
    @staticmethod
    def _contains(text: str, keyword: str) -> bool:
        return re.search(rf"(?<!\w){re.escape(keyword.strip())}(?!\w)", text or "", re.I) is not None

    @classmethod
    def match(cls, candidate: Candidate, job: JobDescription, result: MatchResult) -> MatchResult:
        keywords = []
        seen = set()
        for value in job.keywords or []:
            cleaned = str(value or "").strip()
            key = cleaned.casefold()
            if cleaned and key not in seen:
                seen.add(key)
                keywords.append(cleaned)

        result.total_keywords = len(keywords)
        if not keywords:
            result.keyword_score = 100.0
            result.add_remark("No keyword requirement specified.")
            return result

        matched = [keyword for keyword in keywords if cls._contains(candidate.raw_text, keyword)]
        missing = [keyword for keyword in keywords if keyword not in matched]
        result.matched_keyword_values = matched
        result.missing_keyword_values = missing
        result.matched_keywords = len(matched)
        result.keyword_score = round(len(matched) / len(keywords) * 100, 2)
        result.add_remark(f"Matched {len(matched)} of {len(keywords)} configured keywords.")
        return result
