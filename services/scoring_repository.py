"""
============================================================
RecruitOS

Module      : Enterprise Scoring Repository
Sprint      : 5.5.5
Version     : 1.0.0
Author      : Tamilvanan A

Purpose:
Provides centralized access to scoring configuration stored
in the "Scoring" sheet of RecruitOS_Configuration.xlsx.

Architecture:

RecruitOS_Configuration.xlsx
        ↓
MasterRepository
        ↓
BaseRepository
        ↓
ScoringRepository
        ↓
Score Calculator
        ↓
Matching Engine

Important:
- This repository does NOT read Excel directly.
- MasterRepository is the only workbook access layer.
- Scoring components and weights are configuration-driven.
- No matching component names or weights are hardcoded here.

============================================================
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from config.sheet_names import SCORING
from services.base_repository import BaseRepository
from services.master_repository import MasterRepository


class ScoringRepository(BaseRepository):
    """
    Enterprise Scoring Repository.

    Responsibilities:

        - Load active scoring configuration
        - Validate component names
        - Validate numeric weights
        - Return individual component weights
        - Return all configured weights
        - Return remarks
        - Calculate total configured weight
        - Detect duplicate components
        - Refresh configuration after workbook changes

    Example:

        repository = ScoringRepository()

        repository.get_active_components()

        repository.get_weight("Skill")

        repository.get_all_weights()

        repository.get_total_weight()
    """

    # ========================================================
    # Sheet Configuration
    # ========================================================

    SHEET_NAME = SCORING

    COMPONENT_COLUMN = "Component"

    WEIGHT_COLUMN = "Weight"

    ACTIVE_COLUMN = "Active"

    REMARKS_COLUMN = "Remarks"

    # ========================================================
    # Initialization
    # ========================================================

    def __init__(self) -> None:
        """
        Initialize ScoringRepository.
        """

        self._dataframe = pd.DataFrame()

        self._components: Dict[
            str,
            Dict[str, Any]
        ] = {}

        self.load_repository()

    # ========================================================
    # Repository Loading
    # ========================================================

    def load_repository(self) -> None:
        """
        Load scoring configuration using MasterRepository.

        MasterRepository handles workbook access and caching.

        ScoringRepository handles scoring-specific validation
        and lookup logic.
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

        dataframe = self.filter_active(
            dataframe,
            self.ACTIVE_COLUMN
        )

        dataframe = dataframe.reset_index(
            drop=True
        )

        self._dataframe = dataframe

        self._build_index()

    # ========================================================
    # Structure Validation
    # ========================================================

    def _validate_structure(
        self,
        dataframe: pd.DataFrame
    ) -> None:
        """
        Validate the Scoring sheet structure.

        Required columns:

            Component
            Weight

        Optional columns:

            Active
            Remarks
        """

        if dataframe is None:

            raise ValueError(
                "Scoring sheet could not be loaded."
            )

        required_columns = [

            self.COMPONENT_COLUMN,

            self.WEIGHT_COLUMN

        ]

        missing_columns = [

            column

            for column
            in required_columns

            if column
            not in dataframe.columns

        ]

        if missing_columns:

            raise ValueError(
                "Invalid Scoring sheet. "
                "Required column(s) missing: "
                + ", ".join(
                    missing_columns
                )
            )

    # ========================================================
    # Build Component Index
    # ========================================================

    def _build_index(self) -> None:
        """
        Build fast in-memory scoring component index.

        Example:

            {
                "skill": {
                    "name": "Skill",
                    "weight": 40.0,
                    "remarks": "..."
                }
            }

        Actual component names and values always come from
        RecruitOS_Configuration.xlsx.
        """

        self._components = {}

        for _, row in self._dataframe.iterrows():

            component = str(
                row.get(
                    self.COMPONENT_COLUMN,
                    ""
                )
            ).strip()

            if not component:

                continue

            normalized_component = (
                self.normalize_text(
                    component
                )
            )

            if (
                normalized_component
                in self._components
            ):

                existing = self._components[
                    normalized_component
                ]["name"]

                raise ValueError(
                    "Duplicate active scoring component "
                    "detected in "
                    "RecruitOS_Configuration.xlsx: "
                    f"'{component}'. "
                    f"Existing component: '{existing}'. "
                    "Each active scoring component must "
                    "be unique."
                )

            weight = self._parse_weight(
                row.get(
                    self.WEIGHT_COLUMN,
                    ""
                ),
                component
            )

            remarks = str(
                row.get(
                    self.REMARKS_COLUMN,
                    ""
                )
            ).strip()

            self._components[
                normalized_component
            ] = {

                "name":
                    component,

                "weight":
                    weight,

                "remarks":
                    remarks

            }

    # ========================================================
    # Weight Parsing
    # ========================================================

    @staticmethod
    def _parse_weight(
        value: Any,
        component: str
    ) -> float:
        """
        Convert a configured weight into float.

        Accepted:

            40
            40.0
            "40"
            "40.5"

        Invalid or negative weights raise ValueError.

        This method does not define what the weight SHOULD be.
        It only validates the value entered in configuration.
        """

        if value is None:

            raise ValueError(
                "Missing scoring weight for component: "
                f"'{component}'."
            )

        if isinstance(
            value,
            bool
        ):

            raise ValueError(
                "Invalid scoring weight for component "
                f"'{component}': '{value}'. "
                "Weight must be numeric."
            )

        text = str(
            value
        ).strip()

        if not text:

            raise ValueError(
                "Missing scoring weight for component: "
                f"'{component}'."
            )

        try:

            weight = float(
                text
            )

        except (
            TypeError,
            ValueError
        ) as error:

            raise ValueError(
                "Invalid scoring weight for component "
                f"'{component}': '{value}'. "
                "Weight must be numeric."
            ) from error

        if weight < 0:

            raise ValueError(
                "Invalid scoring weight for component "
                f"'{component}': '{weight}'. "
                "Weight cannot be negative."
            )

        return weight

    # ========================================================
    # Active Components
    # ========================================================

    def get_active_components(
        self
    ) -> List[str]:
        """
        Return all active scoring component names.

        Component names come entirely from configuration.
        """

        components = [

            record["name"]

            for record
            in self._components.values()

        ]

        return components

    # ========================================================
    # Compatibility Alias
    # ========================================================

    def get_components(
        self
    ) -> List[str]:
        """
        Friendly alias for get_active_components().
        """

        return self.get_active_components()

    # ========================================================
    # Validate Component
    # ========================================================

    def is_valid_component(
        self,
        component: str
    ) -> bool:
        """
        Check whether an active scoring component exists.
        """

        normalized = (
            self.normalize_text(
                component
            )
        )

        return (
            normalized
            in self._components
        )

    # ========================================================
    # Get Weight
    # ========================================================

    def get_weight(
        self,
        component: str
    ) -> Optional[float]:
        """
        Return configured weight for a component.

        Returns None when the component does not exist.

        Example:

            repository.get_weight(
                "<configured component>"
            )
        """

        normalized = (
            self.normalize_text(
                component
            )
        )

        if not normalized:

            return None

        record = self._components.get(
            normalized
        )

        if not record:

            return None

        return float(
            record["weight"]
        )

    # ========================================================
    # Require Weight
    # ========================================================

    def require_weight(
        self,
        component: str
    ) -> float:
        """
        Return configured weight.

        Unlike get_weight(), this raises an error when the
        requested component is missing.

        Useful for business services where a configured
        scoring component is mandatory.
        """

        weight = self.get_weight(
            component
        )

        if weight is None:

            raise KeyError(
                "Scoring component not found or inactive: "
                f"'{component}'."
            )

        return weight

    # ========================================================
    # Get All Weights
    # ========================================================

    def get_all_weights(
        self
    ) -> Dict[str, float]:
        """
        Return active scoring configuration as:

            {
                "<Component A>": 40.0,
                "<Component B>": 25.0
            }

        Values are entirely configuration-driven.
        """

        return {

            record["name"]:
                float(
                    record["weight"]
                )

            for record
            in self._components.values()

        }

    # ========================================================
    # Total Weight
    # ========================================================

    def get_total_weight(
        self
    ) -> float:
        """
        Return total weight of all active components.

        The repository does not automatically force a
        particular total during loading.

        This allows configuration validation to be handled
        explicitly by the appropriate business layer.
        """

        return sum(
            float(
                record["weight"]
            )

            for record
            in self._components.values()
        )

    # ========================================================
    # Validate Expected Total
    # ========================================================

    def validate_total_weight(
        self,
        expected_total: float
    ) -> bool:
        """
        Validate configured total against a caller-provided
        expected total.

        No expected total is hardcoded in this repository.

        Example:

            repository.validate_total_weight(100)

        returns True only when active weights total 100.
        """

        try:

            expected = float(
                expected_total
            )

        except (
            TypeError,
            ValueError
        ) as error:

            raise ValueError(
                "Expected scoring total must be numeric."
            ) from error

        actual = self.get_total_weight()

        return abs(
            actual - expected
        ) < 0.000001

    # ========================================================
    # Get Remarks
    # ========================================================

    def get_remarks(
        self,
        component: str
    ) -> Optional[str]:
        """
        Return configured remarks for a component.

        Returns None when the component does not exist.
        """

        details = (
            self.get_component_details(
                component
            )
        )

        if not details:

            return None

        return details[
            "remarks"
        ]

    # ========================================================
    # Component Details
    # ========================================================

    def get_component_details(
        self,
        component: str
    ) -> Optional[Dict[str, Any]]:
        """
        Return complete scoring component metadata.

        Example:

            {
                "name": "<configured component>",
                "weight": 40.0,
                "remarks": "<configured remarks>"
            }
        """

        normalized = (
            self.normalize_text(
                component
            )
        )

        if not normalized:

            return None

        record = self._components.get(
            normalized
        )

        if not record:

            return None

        return {

            "name":
                record["name"],

            "weight":
                float(
                    record["weight"]
                ),

            "remarks":
                record["remarks"]

        }

    # ========================================================
    # All Component Details
    # ========================================================

    def get_all_component_details(
        self
    ) -> List[Dict[str, Any]]:
        """
        Return metadata for every active scoring component.
        """

        return [

            {

                "name":
                    record["name"],

                "weight":
                    float(
                        record["weight"]
                    ),

                "remarks":
                    record["remarks"]

            }

            for record
            in self._components.values()

        ]

    # ========================================================
    # Search Components
    # ========================================================

    def search_components(
        self,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Search active scoring components.

        Searches:

            - Component name
            - Remarks

        Search is case-insensitive and supports partial text.
        """

        normalized_query = (
            self.normalize_text(
                query
            )
        )

        if not normalized_query:

            return []

        results = []

        for record in (
            self._components.values()
        ):

            searchable_values = [

                record["name"],

                record["remarks"]

            ]

            matched = any(

                normalized_query
                in self.normalize_text(
                    value
                )

                for value
                in searchable_values

            )

            if matched:

                results.append(

                    {

                        "name":
                            record["name"],

                        "weight":
                            float(
                                record["weight"]
                            ),

                        "remarks":
                            record["remarks"]

                    }

                )

        return results

    # ========================================================
    # DataFrame Access
    # ========================================================

    def get_dataframe(
        self
    ) -> pd.DataFrame:
        """
        Return a safe copy of the active Scoring DataFrame.
        """

        return self._dataframe.copy()

    # ========================================================
    # Refresh
    # ========================================================

    def refresh(
        self
    ) -> None:
        """
        Reload RecruitOS_Configuration.xlsx and rebuild the
        scoring repository.

        Use after configuration changes.
        """

        MasterRepository.reload()

        self.load_repository()

    # ========================================================
    # Statistics
    # ========================================================

    def total_components(
        self
    ) -> int:
        """
        Return number of active scoring components.
        """

        return len(
            self._components
        )

    # ========================================================
    # Display Summary
    # ========================================================

    def display_summary(
        self
    ) -> None:
        """
        Print ScoringRepository statistics.
        """

        print()

        print("=" * 60)

        print(
            "RecruitOS Enterprise Scoring Repository"
        )

        print("=" * 60)

        print(
            f"Active Components : "
            f"{self.total_components()}"
        )

        print(
            f"Total Weight      : "
            f"{self.get_total_weight()}"
        )

        print("=" * 60)


# ============================================================
# Debug Execution
# ============================================================

if __name__ == "__main__":

    repository = (
        ScoringRepository()
    )

    repository.display_summary()

    print()

    print(
        "Configured Scoring Components"
    )

    print("-" * 60)

    for component in (
        repository.get_all_component_details()
    ):

        print(
            component
        )