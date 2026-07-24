"""Authoritative end-to-end candidate matching orchestration."""
from __future__ import annotations

from JD.jd_model import JobDescription
from models.candidate import Candidate
from models.match_result import MatchResult
from services.configuration_repository import ConfigurationRepository
from services.matching.certification_matcher import CertificationMatcher
from services.matching.education_matcher import EducationMatcher
from services.matching.experience_matcher import ExperienceMatcher
from services.matching.keyword_matcher import KeywordMatcher
from services.matching.score_calculator import ScoreCalculator
from services.matching.skill_matcher import SkillMatcher
from services.recommendation_repository import RecommendationRepository


class MatchingOrchestrator:
    def __init__(
        self,
        score_calculator: ScoreCalculator | None = None,
        recommendation_repository: RecommendationRepository | None = None,
        configuration_repository: ConfigurationRepository | None = None,
    ) -> None:
        self.score_calculator = score_calculator or ScoreCalculator()
        self.recommendations = recommendation_repository or RecommendationRepository()
        self.configuration = configuration_repository or ConfigurationRepository()

        if not self.recommendations.validate_coverage(0, 100):
            raise ValueError(
                "Recommendation ranges must continuously cover scores from 0 through 100."
            )

    def match(self, job: JobDescription, candidate: Candidate, job_id: str = "") -> MatchResult:
        result = SkillMatcher.match(candidate, job)
        result.job_id = job_id
        ExperienceMatcher.match(candidate, job, result)
        EducationMatcher.match(candidate, job, result)
        CertificationMatcher.match(candidate, job, result)
        KeywordMatcher.match(candidate, job, result)
        self.score_calculator.calculate(result)
        result.recommendation = self.recommendations.require_recommendation(result.overall_match_percentage)

        threshold = self.configuration.get_float("Shortlist Minimum Score", None)
        result.shortlisted = threshold is not None and result.overall_match_percentage >= threshold
        result.status = "Shortlisted" if result.shortlisted else "Completed"
        return result

    def match_many(self, job: JobDescription, candidates: list[Candidate], job_id: str = "") -> list[MatchResult]:
        results = [self.match(job, candidate, job_id=job_id) for candidate in candidates]
        results.sort(key=lambda item: item.overall_match_percentage, reverse=True)
        for rank, result in enumerate(results, start=1):
            result.rank = rank
        return results
