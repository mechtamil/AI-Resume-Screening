"""Backward-compatible facade for the authoritative MatchingOrchestrator.

Legacy code may still import ``MatchingEngine`` from this module. New code
should import ``MatchingOrchestrator`` from ``services.matching``.
"""
from __future__ import annotations

from JD.jd_model import JobDescription
from models.candidate import Candidate
from models.match_result import MatchResult
from services.matching.matching_orchestrator import MatchingOrchestrator


class MatchingEngine:
    @staticmethod
    def match(job_description: JobDescription, candidate: Candidate) -> MatchResult:
        return MatchingOrchestrator().match(job_description, candidate)
