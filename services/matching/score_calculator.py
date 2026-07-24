"""Configuration-driven weighted score calculation."""
from __future__ import annotations

from models.match_result import MatchResult
from services.scoring_repository import ScoringRepository


class ScoreCalculator:
    """Calculate overall score from active Scoring-sheet weights.

    Component names are technical integration keys; their weights remain fully
    configurable in Excel. Unknown active components fail fast instead of being
    silently ignored.
    """

    COMPONENT_SCORE_FIELDS = {
        "skill": "skill_score",
        "experience": "experience_score",
        "education": "education_score",
        "certification": "certification_score",
        "keyword": "keyword_score",
    }

    def __init__(self, repository: ScoringRepository | None = None, expected_total: float = 100.0) -> None:
        self.repository = repository or ScoringRepository()
        self.expected_total = float(expected_total)

    def calculate(self, result: MatchResult) -> MatchResult:
        if not self.repository.validate_total_weight(self.expected_total):
            raise ValueError(
                f"Active scoring weights must total {self.expected_total:g}; "
                f"configured total is {self.repository.get_total_weight():g}."
            )

        weighted_total = 0.0
        breakdown: dict[str, float] = {}
        for component, weight in self.repository.get_all_weights().items():
            field = self.COMPONENT_SCORE_FIELDS.get(component.strip().casefold())
            if field is None:
                raise ValueError(
                    f"Unsupported active scoring component '{component}'. Supported technical components: "
                    + ", ".join(sorted(self.COMPONENT_SCORE_FIELDS))
                )
            component_score = float(getattr(result, field))
            contribution = component_score * float(weight) / self.expected_total
            breakdown[component] = round(contribution, 4)
            weighted_total += contribution

        result.weighted_score_breakdown = breakdown
        result.overall_match_percentage = round(weighted_total, 2)
        return result
