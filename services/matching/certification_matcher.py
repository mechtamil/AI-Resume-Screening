"""Certification requirement comparison."""
from __future__ import annotations

from JD.jd_model import JobDescription
from models.candidate import Candidate
from models.match_result import MatchResult


class CertificationMatcher:
    @staticmethod
    def match(candidate: Candidate, job: JobDescription, result: MatchResult) -> MatchResult:
        candidate_map = {str(v).strip().casefold(): str(v).strip() for v in candidate.certifications if str(v).strip()}
        required_map = {str(v).strip().casefold(): str(v).strip() for v in job.certifications if str(v).strip()}
        if not required_map:
            result.certification_match = True
            result.certification_score = 100.0
            result.add_remark("No certification requirement specified.")
            return result
        matched = sorted(set(candidate_map) & set(required_map))
        missing = sorted(set(required_map) - set(candidate_map))
        result.matched_certifications = [required_map[k] for k in matched]
        result.missing_certifications = [required_map[k] for k in missing]
        result.certification_score = round(len(matched) / len(required_map) * 100, 2)
        result.certification_match = not missing
        result.add_remark(f"Matched {len(matched)} of {len(required_map)} required certifications.")
        return result
