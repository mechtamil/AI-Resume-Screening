"""Education requirement comparison."""
from __future__ import annotations

from JD.jd_model import JobDescription
from models.candidate import Candidate
from models.match_result import MatchResult


class EducationMatcher:
    @staticmethod
    def match(candidate: Candidate, job: JobDescription, result: MatchResult) -> MatchResult:
        candidate_values = {str(v).strip().casefold() for v in candidate.education if str(v).strip()}
        required_values = {str(v).strip().casefold() for v in job.education if str(v).strip()}
        if not required_values:
            result.education_match = True
            result.education_score = 100.0
            result.add_remark("No education requirement specified.")
        elif candidate_values & required_values:
            result.education_match = True
            result.education_score = 100.0
            result.add_remark("Candidate satisfies the education requirement.")
        else:
            result.education_match = False
            result.education_score = 0.0
            result.add_remark("Candidate does not satisfy the configured education requirement.")
        return result
