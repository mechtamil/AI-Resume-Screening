"""Mandatory/preferred skill comparison."""
from __future__ import annotations

from JD.jd_model import JobDescription
from models.candidate import Candidate
from models.match_result import MatchResult


class SkillMatcher:
    @staticmethod
    def _canonical_map(values: list[str]) -> dict[str, str]:
        return {str(v).strip().casefold(): str(v).strip() for v in values or [] if str(v).strip()}

    @classmethod
    def match(cls, candidate: Candidate, job: JobDescription, result: MatchResult | None = None) -> MatchResult:
        result = result or MatchResult()
        result.candidate_name = candidate.full_name
        result.email = candidate.email
        result.phone = candidate.phone
        result.source_file = candidate.source_file
        result.job_title = job.job_title

        candidate_map = cls._canonical_map(candidate.technical_skills)
        mandatory_map = cls._canonical_map(job.mandatory_skills)
        preferred_map = cls._canonical_map(job.preferred_skills)

        matched_keys = sorted(set(candidate_map) & set(mandatory_map))
        missing_keys = sorted(set(mandatory_map) - set(candidate_map))
        preferred_matched = sorted(set(candidate_map) & set(preferred_map))
        preferred_missing = sorted(set(preferred_map) - set(candidate_map))
        required_keys = set(mandatory_map) | set(preferred_map)
        additional_keys = sorted(set(candidate_map) - required_keys)

        result.matched_skills = [mandatory_map[k] for k in matched_keys]
        result.missing_skills = [mandatory_map[k] for k in missing_keys]
        result.matched_preferred_skills = [preferred_map[k] for k in preferred_matched]
        result.missing_preferred_skills = [preferred_map[k] for k in preferred_missing]
        result.additional_skills = [candidate_map[k] for k in additional_keys]

        if mandatory_map:
            result.skill_score = round(len(matched_keys) / len(mandatory_map) * 100, 2)
            result.add_remark(f"Matched {len(matched_keys)} of {len(mandatory_map)} mandatory skills.")
        else:
            result.skill_score = 100.0
            result.add_remark("No mandatory skill requirement specified.")
        if preferred_map:
            result.add_remark(f"Matched {len(preferred_matched)} of {len(preferred_map)} preferred skills.")
        return result
