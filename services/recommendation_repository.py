"""
============================================================
RecruitOS

Module      : Enterprise Recommendation Repository
Sprint      : 5.5.6
Version     : 1.0.0
Author      : Tamilvanan A

Purpose:
Provides centralized access to recommendation rules stored
in the "Recommendation" sheet of
RecruitOS_Configuration.xlsx.

Architecture:

RecruitOS_Configuration.xlsx
        ↓
MasterRepository
        ↓
BaseRepository
        ↓
RecommendationRepository
        ↓
Score Calculator
        ↓
Matching Engine

Important:
- This repository does NOT read Excel directly.
- MasterRepository is the workbook access layer.
- Recommendation labels and score ranges are entirely
  configuration-driven.
- No recommendation thresholds are hardcoded in Python.

============================================================
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from config.sheet_names import RECOMMENDATION
from services.base_repository import BaseRepository
from services.master_repository import MasterRepository


class RecommendationRepository(BaseRepository):
    """
    Enterprise Recommendation Repository.

    Responsibilities:

        - Load recommendation configuration
        - Validate score ranges
        - Detect overlapping ranges
        - Detect duplicate recommendation labels
        - Resolve a score to a recommendation
        - Return recommendation metadata
        - Search recommendation rules
        - Refresh configuration

    Expected worksheet structure:

        Minimum Score
        Maximum Score
        Recommendation

    Optional columns:

        Active
        Remarks
    """

    SHEET_NAME = RECOMMENDATION

    MINIMUM_SCORE_COLUMN = "Minimum Score"

    MAXIMUM_SCORE_COLUMN = "Maximum Score"

    RECOMMENDATION_COLUMN = "Recommendation"

    ACTIVE_COLUMN = "Active"

    REMARKS_COLUMN = "Remarks"

    def __init__(self) -> None:
        """
        Initialize RecommendationRepository.
        """

        self._dataframe = pd.DataFrame()

        self._ranges: List[Dict[str, Any]] = []

        self._recommendations_by_name: Dict[
            str,
            Dict[str, Any]
        ] = {}

        self.load_repository()

    # ========================================================
    # Repository Loading
    # ========================================================

    def load_repository(self) -> None:
        """
        Load recommendation configuration through
        MasterRepository.
        """

        dataframe = MasterRepository.get_sheet(
            self.SHEET_NAME
        )

        self._validate_structure(
            dataframe
        )

        dataframe = dataframe.copy()

        dataframe.fillna(
            "",
            inplace=True
        )

        # Active is optional.
        #
        # If the column exists, only active rules are loaded.
        # If it does not exist, BaseRepository returns all rows.

        dataframe = self.filter_active(
            dataframe,
            self.ACTIVE_COLUMN
        )

        dataframe = dataframe.reset_index(
            drop=True
        )

        self._dataframe = dataframe

        self._build_repository()

    # ========================================================
    # Structure Validation
    # ========================================================

    def _validate_structure(
        self,
        dataframe: pd.DataFrame
    ) -> None:
        """
        Validate required Recommendation sheet columns.
        """

        if dataframe is None:

            raise ValueError(
                "Recommendation sheet could not be loaded."
            )

        required_columns = [

            self.MINIMUM_SCORE_COLUMN,

            self.MAXIMUM_SCORE_COLUMN,

            self.RECOMMENDATION_COLUMN

        ]

        missing_columns = [

            column

            for column in required_columns

            if column not in dataframe.columns

        ]

        if missing_columns:

            raise ValueError(
                "Invalid Recommendation sheet. "
                "Required column(s) missing: "
                + ", ".join(
                    missing_columns
                )
            )

    # ========================================================
    # Build Repository
    # ========================================================

    def _build_repository(self) -> None:
        """
        Build recommendation rule indexes and validate ranges.
        """

        self._ranges = []

        self._recommendations_by_name = {}

        for _, row in self._dataframe.iterrows():

            recommendation = str(
                row.get(
                    self.RECOMMENDATION_COLUMN,
                    ""
                )
            ).strip()

            # Completely blank rows are ignored.

            if not recommendation:

                continue

            minimum_score = self._parse_score(
                row.get(
                    self.MINIMUM_SCORE_COLUMN,
                    ""
                ),
                self.MINIMUM_SCORE_COLUMN,
                recommendation
            )

            maximum_score = self._parse_score(
                row.get(
                    self.MAXIMUM_SCORE_COLUMN,
                    ""
                ),
                self.MAXIMUM_SCORE_COLUMN,
                recommendation
            )

            if minimum_score > maximum_score:

                raise ValueError(
                    "Invalid recommendation score range for "
                    f"'{recommendation}'. "
                    f"Minimum Score ({minimum_score}) cannot "
                    f"be greater than Maximum Score "
                    f"({maximum_score})."
                )

            normalized_name = self.normalize_text(
                recommendation
            )

            if (
                normalized_name
                in self._recommendations_by_name
            ):

                raise ValueError(
                    "Duplicate active recommendation label "
                    "detected in "
                    "RecruitOS_Configuration.xlsx: "
                    f"'{recommendation}'. "
                    "Each active recommendation label must "
                    "be unique."
                )

            remarks = str(
                row.get(
                    self.REMARKS_COLUMN,
                    ""
                )
            ).strip()

            record = {

                "recommendation":
                    recommendation,

                "minimum_score":
                    minimum_score,

                "maximum_score":
                    maximum_score,

                "remarks":
                    remarks

            }

            self._ranges.append(
                record
            )

            self._recommendations_by_name[
                normalized_name
            ] = record

        # Sort by minimum score for deterministic validation.

        self._ranges.sort(
            key=lambda item:
                item["minimum_score"]
        )

        self._validate_overlapping_ranges()

    # ========================================================
    # Score Parsing
    # ========================================================

    @staticmethod
    def _parse_score(
        value: Any,
        column_name: str,
        recommendation: str
    ) -> float:
        """
        Convert configured score boundary to float.

        This method does not impose hardcoded score limits.

        The scoring scale remains controlled by configuration
        and the business layer.
        """

        if value is None:

            raise ValueError(
                f"Missing {column_name} for recommendation "
                f"'{recommendation}'."
            )

        if isinstance(
            value,
            bool
        ):

            raise ValueError(
                f"Invalid {column_name} for recommendation "
                f"'{recommendation}': '{value}'. "
                "Score must be numeric."
            )

        text = str(
            value
        ).strip()

        if not text:

            raise ValueError(
                f"Missing {column_name} for recommendation "
                f"'{recommendation}'."
            )

        try:

            return float(
                text
            )

        except (
            TypeError,
            ValueError
        ) as error:

            raise ValueError(
                f"Invalid {column_name} for recommendation "
                f"'{recommendation}': '{value}'. "
                "Score must be numeric."
            ) from error

    # ========================================================
    # Overlap Validation
    # ========================================================

    def _validate_overlapping_ranges(
        self
    ) -> None:
        """
        Ensure recommendation ranges do not overlap.

        Because both boundaries are inclusive:

            0 - 60
            60 - 80

        is considered overlapping at score 60.

        Configuration should instead define non-overlapping
        boundaries appropriate for the scoring precision used
        by RecruitOS.
        """

        if len(
            self._ranges
        ) <= 1:

            return

        previous = self._ranges[0]

        for current in self._ranges[1:]:

            if (
                current["minimum_score"]
                <= previous["maximum_score"]
            ):

                raise ValueError(
                    "Overlapping recommendation ranges "
                    "detected. "
                    f"'{previous['recommendation']}' "
                    f"({previous['minimum_score']} - "
                    f"{previous['maximum_score']}) overlaps "
                    f"with "
                    f"'{current['recommendation']}' "
                    f"({current['minimum_score']} - "
                    f"{current['maximum_score']}). "
                    "Please correct the Recommendation sheet."
                )

            previous = current

    # ========================================================
    # Recommendation Resolution
    # ========================================================

    def get_recommendation(
        self,
        score: Any
    ) -> Optional[str]:
        """
        Resolve a score to its configured recommendation.

        Returns None when no configured range contains the
        supplied score.
        """

        numeric_score = self._parse_input_score(
            score
        )

        for record in self._ranges:

            if (
                record["minimum_score"]
                <= numeric_score
                <= record["maximum_score"]
            ):

                return record[
                    "recommendation"
                ]

        return None

    # ========================================================
    # Required Recommendation
    # ========================================================

    def require_recommendation(
        self,
        score: Any
    ) -> str:
        """
        Resolve recommendation and raise LookupError when
        the score is not covered by any configured range.
        """

        recommendation = (
            self.get_recommendation(
                score
            )
        )

        if recommendation is None:

            raise LookupError(
                "No recommendation range configured for "
                f"score: {score}."
            )

        return recommendation

    # ========================================================
    # Input Score Parsing
    # ========================================================

    @staticmethod
    def _parse_input_score(
        score: Any
    ) -> float:
        """
        Validate a runtime score supplied by another service.
        """

        if score is None:

            raise ValueError(
                "Score cannot be None."
            )

        if isinstance(
            score,
            bool
        ):

            raise ValueError(
                "Score must be numeric."
            )

        try:

            return float(
                score
            )

        except (
            TypeError,
            ValueError
        ) as error:

            raise ValueError(
                f"Invalid score: '{score}'. "
                "Score must be numeric."
            ) from error

    # ========================================================
    # Get All Recommendation Rules
    # ========================================================

    def get_all_recommendations(
        self
    ) -> List[Dict[str, Any]]:
        """
        Return all configured recommendation rules.

        A safe copy is returned.
        """

        return [

            {

                "recommendation":
                    record[
                        "recommendation"
                    ],

                "minimum_score":
                    float(
                        record[
                            "minimum_score"
                        ]
                    ),

                "maximum_score":
                    float(
                        record[
                            "maximum_score"
                        ]
                    ),

                "remarks":
                    record[
                        "remarks"
                    ]

            }

            for record in self._ranges

        ]

    # ========================================================
    # Recommendation Names
    # ========================================================

    def get_recommendation_names(
        self
    ) -> List[str]:
        """
        Return configured recommendation labels.
        """

        return [

            record[
                "recommendation"
            ]

            for record in self._ranges

        ]

    # ========================================================
    # Validation
    # ========================================================

    def is_valid_recommendation(
        self,
        recommendation: str
    ) -> bool:
        """
        Check whether a recommendation label exists.
        """

        normalized = self.normalize_text(
            recommendation
        )

        return (
            normalized
            in self._recommendations_by_name
        )

    # ========================================================
    # Recommendation Details
    # ========================================================

    def get_recommendation_details(
        self,
        recommendation: str
    ) -> Optional[Dict[str, Any]]:
        """
        Return metadata for a recommendation label.
        """

        normalized = self.normalize_text(
            recommendation
        )

        if not normalized:

            return None

        record = (
            self._recommendations_by_name.get(
                normalized
            )
        )

        if not record:

            return None

        return {

            "recommendation":
                record[
                    "recommendation"
                ],

            "minimum_score":
                float(
                    record[
                        "minimum_score"
                    ]
                ),

            "maximum_score":
                float(
                    record[
                        "maximum_score"
                    ]
                ),

            "remarks":
                record[
                    "remarks"
                ]

        }

    # ========================================================
    # Score Range
    # ========================================================

    def get_score_range(
        self,
        recommendation: str
    ) -> Optional[Dict[str, float]]:
        """
        Return minimum and maximum score for a recommendation.
        """

        details = (
            self.get_recommendation_details(
                recommendation
            )
        )

        if not details:

            return None

        return {

            "minimum_score":
                details[
                    "minimum_score"
                ],

            "maximum_score":
                details[
                    "maximum_score"
                ]

        }

    # ========================================================
    # Remarks
    # ========================================================

    def get_remarks(
        self,
        recommendation: str
    ) -> Optional[str]:
        """
        Return configured remarks.
        """

        details = (
            self.get_recommendation_details(
                recommendation
            )
        )

        if not details:

            return None

        return details[
            "remarks"
        ]

    # ========================================================
    # Search
    # ========================================================

    def search_recommendations(
        self,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Search recommendation labels and remarks.

        Search is case-insensitive and supports partial match.
        """

        normalized_query = (
            self.normalize_text(
                query
            )
        )

        if not normalized_query:

            return []

        results = []

        for record in self._ranges:

            searchable_values = [

                record[
                    "recommendation"
                ],

                record[
                    "remarks"
                ]

            ]

            matched = any(

                normalized_query
                in self.normalize_text(
                    value
                )

                for value in searchable_values

            )

            if matched:

                results.append(

                    {

                        "recommendation":
                            record[
                                "recommendation"
                            ],

                        "minimum_score":
                            float(
                                record[
                                    "minimum_score"
                                ]
                            ),

                        "maximum_score":
                            float(
                                record[
                                    "maximum_score"
                                ]
                            ),

                        "remarks":
                            record[
                                "remarks"
                            ]

                    }

                )

        return results

    # ========================================================
    # Coverage Check
    # ========================================================

    def is_score_covered(
        self,
        score: Any
    ) -> bool:
        """
        Check whether a score falls within any configured
        recommendation range.
        """

        return (
            self.get_recommendation(
                score
            )
            is not None
        )

    # ========================================================
    # Statistics
    # ========================================================

    def total_recommendations(
        self
    ) -> int:
        """
        Return number of active recommendation rules.
        """

        return len(
            self._ranges
        )

    # ========================================================
    # DataFrame Access
    # ========================================================

    def get_dataframe(
        self
    ) -> pd.DataFrame:
        """
        Return a safe copy of the active Recommendation
        DataFrame.
        """

        return self._dataframe.copy()

    # ========================================================
    # Refresh
    # ========================================================

    def refresh(
        self
    ) -> None:
        """
        Reload RecruitOS_Configuration.xlsx and rebuild
        RecommendationRepository.
        """

        MasterRepository.reload()

        self.load_repository()

    # ========================================================
    # Display Summary
    # ========================================================

    def display_summary(
        self
    ) -> None:
        """
        Display repository statistics.
        """

        print()

        print("=" * 60)

        print(
            "RecruitOS Enterprise Recommendation Repository"
        )

        print("=" * 60)

        print(
            f"Recommendation Rules : "
            f"{self.total_recommendations()}"
        )

        print("=" * 60)


# ============================================================
# Debug Execution
# ============================================================

if __name__ == "__main__":

    repository = (
        RecommendationRepository()
    )

    repository.display_summary()

    print()

    print(
        "Configured Recommendation Rules"
    )

    print("-" * 60)

    for rule in (
        repository.get_all_recommendations()
    ):

        print(
            rule
        )