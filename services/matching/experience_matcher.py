"""Experience requirement comparison."""
from __future__ import annotations

from JD.jd_model import JobDescription
from models.candidate import Candidate
from models.match_result import MatchResult


class ExperienceMatcher:
    @staticmethod
    def match(candidate: Candidate, job: JobDescription, result: MatchResult) -> MatchResult:
        required = max(float(job.experience_min or 0), 0.0)
        maximum = max(float(job.experience_max or 0), required)
        candidate_exp = max(float(candidate.total_experience or 0), 0.0)
        result.required_experience = required
        result.maximum_experience = maximum
        result.candidate_experience = candidate_exp

        if required <= 0:
            result.experience_match = True
            result.experience_score = 100.0
            result.add_remark("No minimum experience requirement specified.")
        elif candidate_exp >= required:
            result.experience_match = True
            result.experience_score = 100.0
            result.add_remark(f"Candidate meets the minimum experience requirement of {required:g} years.")
        else:
            result.experience_match = False
            result.experience_score = round(candidate_exp / required * 100, 2)
            result.add_remark(f"Candidate is below the minimum experience requirement by {required - candidate_exp:g} years.")
        return result
