"""Configuration-driven score-to-recommendation repository."""
from __future__ import annotations

from typing import Any

import pandas as pd

from config.sheet_names import RECOMMENDATION
from services.base_repository import BaseRepository
from services.master_repository import MasterRepository


class RecommendationRepository(BaseRepository):
    """Resolve scores using contiguous half-open configured ranges.

    Ranges are interpreted as ``minimum <= score < maximum`` except the final
    highest range, whose maximum is inclusive. This allows adjacent ranges such
    as 0-60, 60-75, 75-90, 90-100 to cover decimal scores without overlap.
    """

    SHEET_NAME = RECOMMENDATION
    MINIMUM_SCORE_COLUMN = "Minimum Score"
    MAXIMUM_SCORE_COLUMN = "Maximum Score"
    RECOMMENDATION_COLUMN = "Recommendation"
    ACTIVE_COLUMN = "Active"
    REMARKS_COLUMN = "Remarks"

    def __init__(self) -> None:
        self._dataframe = pd.DataFrame()
        self._ranges: list[dict[str, Any]] = []
        self._by_name: dict[str, dict[str, Any]] = {}
        self.load_repository()

    def load_repository(self) -> None:
        dataframe = MasterRepository.get_sheet(self.SHEET_NAME).copy().fillna("")
        for column in (
            self.MINIMUM_SCORE_COLUMN,
            self.MAXIMUM_SCORE_COLUMN,
            self.RECOMMENDATION_COLUMN,
        ):
            if column not in dataframe.columns:
                raise ValueError(f"Recommendation sheet must contain '{column}'.")
        dataframe = self.filter_active(dataframe, self.ACTIVE_COLUMN).reset_index(drop=True)
        self._dataframe = dataframe
        self._build_repository()

    @staticmethod
    def _parse_score(value: Any, column_name: str, recommendation: str) -> float:
        if value is None or isinstance(value, bool) or str(value).strip() == "":
            raise ValueError(f"Missing {column_name} for '{recommendation}'.")
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{column_name} for '{recommendation}' must be numeric.") from exc

    @staticmethod
    def _parse_input_score(score: Any) -> float:
        if score is None or isinstance(score, bool):
            raise ValueError("Score must be numeric.")
        try:
            return float(score)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid score '{score}'.") from exc

    def _build_repository(self) -> None:
        self._ranges = []
        self._by_name = {}
        for _, row in self._dataframe.iterrows():
            name = str(row.get(self.RECOMMENDATION_COLUMN, "")).strip()
            if not name:
                continue
            minimum = self._parse_score(row.get(self.MINIMUM_SCORE_COLUMN, ""), self.MINIMUM_SCORE_COLUMN, name)
            maximum = self._parse_score(row.get(self.MAXIMUM_SCORE_COLUMN, ""), self.MAXIMUM_SCORE_COLUMN, name)
            if minimum >= maximum:
                raise ValueError(f"Recommendation '{name}' must have Minimum Score < Maximum Score.")
            key = self.normalize_text(name)
            if key in self._by_name:
                raise ValueError(f"Duplicate active recommendation '{name}'.")
            record = {
                "recommendation": name,
                "minimum_score": minimum,
                "maximum_score": maximum,
                "remarks": str(row.get(self.REMARKS_COLUMN, "")).strip(),
            }
            self._ranges.append(record)
            self._by_name[key] = record
        self._ranges.sort(key=lambda item: item["minimum_score"])
        self._validate_ranges()

    def _validate_ranges(self) -> None:
        for previous, current in zip(self._ranges, self._ranges[1:]):
            if current["minimum_score"] < previous["maximum_score"]:
                raise ValueError(
                    f"Recommendation ranges overlap: '{previous['recommendation']}' and "
                    f"'{current['recommendation']}'."
                )

    def validate_coverage(self, minimum_score: float = 0.0, maximum_score: float = 100.0) -> bool:
        if not self._ranges:
            return False
        if abs(self._ranges[0]["minimum_score"] - float(minimum_score)) > 1e-9:
            return False
        if abs(self._ranges[-1]["maximum_score"] - float(maximum_score)) > 1e-9:
            return False
        return all(
            abs(previous["maximum_score"] - current["minimum_score"]) < 1e-9
            for previous, current in zip(self._ranges, self._ranges[1:])
        )

    def get_recommendation(self, score: Any) -> str | None:
        numeric = self._parse_input_score(score)
        for index, record in enumerate(self._ranges):
            is_last = index == len(self._ranges) - 1
            if record["minimum_score"] <= numeric < record["maximum_score"]:
                return record["recommendation"]
            if is_last and numeric == record["maximum_score"]:
                return record["recommendation"]
        return None

    def require_recommendation(self, score: Any) -> str:
        recommendation = self.get_recommendation(score)
        if recommendation is None:
            raise LookupError(f"No recommendation range covers score {score}.")
        return recommendation

    def get_all_recommendations(self) -> list[dict[str, Any]]:
        return [dict(record) for record in self._ranges]

    def get_recommendation_names(self) -> list[str]:
        return [record["recommendation"] for record in self._ranges]

    def is_valid_recommendation(self, recommendation: str) -> bool:
        return self.normalize_text(recommendation) in self._by_name

    def get_recommendation_details(self, recommendation: str) -> dict[str, Any] | None:
        record = self._by_name.get(self.normalize_text(recommendation))
        return dict(record) if record else None

    def get_score_range(self, recommendation: str) -> dict[str, float] | None:
        details = self.get_recommendation_details(recommendation)
        if not details:
            return None
        return {"minimum_score": details["minimum_score"], "maximum_score": details["maximum_score"]}

    def get_remarks(self, recommendation: str) -> str | None:
        details = self.get_recommendation_details(recommendation)
        return details["remarks"] if details else None

    def search_recommendations(self, query: str) -> list[dict[str, Any]]:
        target = self.normalize_text(query)
        if not target:
            return []
        return [
            dict(record)
            for record in self._ranges
            if target in self.normalize_text(record["recommendation"])
            or target in self.normalize_text(record["remarks"])
        ]

    def is_score_covered(self, score: Any) -> bool:
        return self.get_recommendation(score) is not None

    def total_recommendations(self) -> int:
        return len(self._ranges)

    def get_dataframe(self) -> pd.DataFrame:
        return self._dataframe.copy()

    def refresh(self) -> None:
        MasterRepository.reload()
        self.load_repository()

    def display_summary(self) -> None:
        print("\nRecruitOS Enterprise Recommendation Repository")
        print("-" * 60)
        print(f"Recommendation Rules : {self.total_recommendations()}")
        print(f"Continuous 0-100     : {self.validate_coverage(0, 100)}")
        print("-" * 60)
