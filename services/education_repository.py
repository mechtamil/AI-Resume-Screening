"""
============================================================
RecruitOS

Module      : Enterprise Education Repository
Sprint      : 5.5.3
Version     : 1.0.0
Author      : Tamilvanan A

Purpose:
Provides centralized access to education master data stored
in the "Education" sheet of RecruitOS_Configuration.xlsx.

Architecture:

RecruitOS_Configuration.xlsx
        ↓
MasterRepository
        ↓
BaseRepository
        ↓
EducationRepository
        ↓
Resume Parser
JD Parser
Education Matcher
Analytics
AI Services

Important:
This repository does NOT read Excel directly.

All workbook access must go through MasterRepository.

No degree names or education business data are hardcoded
inside the source code.

============================================================
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from config.sheet_names import EDUCATION
from services.base_repository import BaseRepository
from services.master_repository import MasterRepository


PriorityType = Optional[Union[int, float, str]]


class EducationRepository(BaseRepository):
    """
    Enterprise Education Repository.

    Provides:

        - Standard education lookup
        - Alias normalization
        - Education validation
        - Priority lookup
        - Search
        - Active/inactive filtering
        - Education metadata access
        - Repository refresh

    Example:

        repository = EducationRepository()

        repository.get_all_degrees()

        repository.normalize_degree("BE")

        repository.is_valid_degree("Bachelor of Engineering")

        repository.get_priority("BE")
    """

    # ========================================================
    # Sheet Configuration
    # ========================================================

    SHEET_NAME = EDUCATION

    EDUCATION_COLUMN = "Education"

    ALIAS_COLUMN = "Alias"

    PRIORITY_COLUMN = "Priority"

    ACTIVE_COLUMN = "Active"

    # ========================================================
    # Initialization
    # ========================================================

    def __init__(self) -> None:
        """
        Initialize EducationRepository.
        """

        self._dataframe = pd.DataFrame()

        self._education_by_name: Dict[str, Dict[str, Any]] = {}

        self._alias_to_standard: Dict[str, str] = {}

        self.load_repository()

    # ========================================================
    # Repository Loading
    # ========================================================

    def load_repository(self) -> None:
        """
        Load education master data from MasterRepository.

        MasterRepository is responsible for:

            - Loading RecruitOS_Configuration.xlsx
            - Workbook caching
            - Providing individual sheets

        EducationRepository only handles education-specific
        data access and normalization.
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

        # Filter only active records when the Active column
        # exists in the workbook.

        dataframe = self.filter_active(
            dataframe,
            self.ACTIVE_COLUMN
        )

        dataframe = dataframe.reset_index(
            drop=True
        )

        self._dataframe = dataframe

        self._build_indexes()

    # ========================================================
    # Structure Validation
    # ========================================================

    def _validate_structure(
        self,
        dataframe: pd.DataFrame
    ) -> None:
        """
        Validate Education sheet structure.

        Required:

            Education

        Optional:

            Alias
            Priority
            Active

        Only the Education column is mandatory so that
        RecruitOS can support simple or extended configuration
        workbooks.
        """

        if dataframe is None:

            raise ValueError(
                "Education sheet could not be loaded."
            )

        if self.EDUCATION_COLUMN not in dataframe.columns:

            raise ValueError(
                "Invalid Education sheet. "
                f"Required column missing: "
                f"'{self.EDUCATION_COLUMN}'"
            )

    # ========================================================
    # Index Building
    # ========================================================

    def _build_indexes(self) -> None:
        """
        Build fast in-memory education indexes.

        Index 1:

            normalized education name
                ↓
            education metadata

        Index 2:

            normalized alias
                ↓
            standard education name
        """

        self._education_by_name = {}

        self._alias_to_standard = {}

        for _, row in self._dataframe.iterrows():

            education_name = str(
                row.get(
                    self.EDUCATION_COLUMN,
                    ""
                )
            ).strip()

            if not education_name:

                continue

            normalized_name = self.normalize_text(
                education_name
            )

            aliases = self._parse_aliases(
                row.get(
                    self.ALIAS_COLUMN,
                    ""
                )
            )

            priority = self._parse_priority(
                row.get(
                    self.PRIORITY_COLUMN,
                    ""
                )
            )

            record = {

                "name": education_name,

                "aliases": aliases,

                "priority": priority

            }

            self._education_by_name[
                normalized_name
            ] = record

            # The standard education name itself must always
            # resolve to the standard education name.

            self._register_alias(
                education_name,
                education_name
            )

            # Register every configured alias.

            for alias in aliases:

                self._register_alias(
                    alias,
                    education_name
                )

    # ========================================================
    # Alias Registration
    # ========================================================

    def _register_alias(
        self,
        alias: str,
        standard_name: str
    ) -> None:
        """
        Register an education alias.

        Duplicate aliases pointing to the same standard degree
        are allowed.

        Ambiguous aliases pointing to different standard degrees
        raise an error because RecruitOS would otherwise be
        unable to normalize the degree reliably.

        Example of invalid configuration:

            Bachelor of Engineering -> BE

            Bachelor of Economics   -> BE

        The alias "BE" would be ambiguous.
        """

        normalized_alias = self.normalize_text(
            alias
        )

        if not normalized_alias:

            return

        existing_standard = self._alias_to_standard.get(
            normalized_alias
        )

        if (
            existing_standard
            and self.normalize_text(existing_standard)
            != self.normalize_text(standard_name)
        ):

            raise ValueError(
                "Duplicate or ambiguous education alias "
                f"detected: '{alias}'. "
                f"It is mapped to both "
                f"'{existing_standard}' and "
                f"'{standard_name}'. "
                "Please correct the Education sheet in "
                "RecruitOS_Configuration.xlsx."
            )

        self._alias_to_standard[
            normalized_alias
        ] = standard_name

    # ========================================================
    # Alias Parsing
    # ========================================================

    @classmethod
    def _parse_aliases(
        cls,
        value: Any
    ) -> List[str]:
        """
        Parse education aliases from Excel.

        Supported separators:

            ;
            ,
            |

        Example:

            BE;B.E.;B.E

        becomes:

            [
                "BE",
                "B.E.",
                "B.E"
            ]

        Duplicate aliases are automatically removed.
        """

        if value is None:

            return []

        text = str(value).strip()

        if not text:

            return []

        parts = re.split(
            r"[;,|]",
            text
        )

        aliases = []

        seen = set()

        for part in parts:

            alias = part.strip()

            normalized_alias = cls.normalize_text(
                alias
            )

            if (
                normalized_alias
                and normalized_alias not in seen
            ):

                seen.add(
                    normalized_alias
                )

                aliases.append(
                    alias
                )

        return aliases

    # ========================================================
    # Priority Parsing
    # ========================================================

    @staticmethod
    def _parse_priority(
        value: Any
    ) -> PriorityType:
        """
        Parse education priority.

        Supports:

            Integer
            Decimal
            Text
            Blank

        Examples:

            1       -> 1
            2.5     -> 2.5
            "High"  -> "High"
            Blank   -> None

        The repository does not hardcode priority rules.

        The meaning of Priority remains configuration-driven.
        """

        if value is None:

            return None

        if isinstance(value, bool):

            return str(value)

        if isinstance(value, int):

            return value

        if isinstance(value, float):

            if pd.isna(value):

                return None

            if value.is_integer():

                return int(value)

            return value

        text = str(value).strip()

        if not text:

            return None

        try:

            numeric = float(text)

            if numeric.is_integer():

                return int(numeric)

            return numeric

        except ValueError:

            return text

    # ========================================================
    # Get All Degrees
    # ========================================================

    def get_all_degrees(
        self
    ) -> List[str]:
        """
        Return all active standardized education names.
        """

        degrees = [

            record["name"]

            for record
            in self._education_by_name.values()

        ]

        return sorted(
            degrees,
            key=str.lower
        )

    # ========================================================
    # Backward/Friendly Alias
    # ========================================================

    def get_degree_names(
        self
    ) -> List[str]:
        """
        Friendly alias for get_all_degrees().
        """

        return self.get_all_degrees()

    # ========================================================
    # Total Degrees
    # ========================================================

    def total_degrees(
        self
    ) -> int:
        """
        Return number of active configured education records.
        """

        return len(
            self._education_by_name
        )

    # ========================================================
    # Find Standard Degree
    # ========================================================

    def find_standard_degree(
        self,
        value: str
    ) -> Optional[str]:
        """
        Convert a degree or alias into its configured
        standard education name.

        Example:

            Input:
                BE

            Configuration:
                Education = Bachelor of Engineering
                Alias     = BE;B.E.

            Returns:
                Bachelor of Engineering
        """

        normalized = self.normalize_text(
            value
        )

        if not normalized:

            return None

        return self._alias_to_standard.get(
            normalized
        )

    # ========================================================
    # Normalize Degree
    # ========================================================

    def normalize_degree(
        self,
        value: str
    ) -> Optional[str]:
        """
        Preferred API for education normalization.

        Returns the configured standard education name.

        Unknown education values return None.
        """

        return self.find_standard_degree(
            value
        )

    # ========================================================
    # Validate Degree
    # ========================================================

    def is_valid_degree(
        self,
        value: str
    ) -> bool:
        """
        Check whether a degree or alias exists in the active
        Education configuration.
        """

        return (
            self.find_standard_degree(
                value
            )
            is not None
        )

    # ========================================================
    # Get Aliases
    # ========================================================

    def get_aliases(
        self,
        value: str
    ) -> List[str]:
        """
        Return configured aliases for an education record.

        Input may be either:

            - Standard education name
            - Alias
        """

        details = self.get_degree_details(
            value
        )

        if not details:

            return []

        return list(
            details["aliases"]
        )

    # ========================================================
    # Get Priority
    # ========================================================

    def get_priority(
        self,
        value: str
    ) -> PriorityType:
        """
        Return configured education priority.

        No priority logic is hardcoded.

        Whatever value is entered in the Priority column is
        returned after basic type conversion.
        """

        details = self.get_degree_details(
            value
        )

        if not details:

            return None

        return details[
            "priority"
        ]

    # ========================================================
    # Degree Details
    # ========================================================

    def get_degree_details(
        self,
        value: str
    ) -> Optional[Dict[str, Any]]:
        """
        Return complete metadata for an education record.

        Example:

        {
            "name": "Bachelor of Engineering",
            "aliases": [
                "BE",
                "B.E."
            ],
            "priority": 1
        }
        """

        standard_name = (
            self.find_standard_degree(
                value
            )
        )

        if not standard_name:

            return None

        normalized_standard = (
            self.normalize_text(
                standard_name
            )
        )

        record = (
            self._education_by_name.get(
                normalized_standard
            )
        )

        if not record:

            return None

        return {

            "name":
                record["name"],

            "aliases":
                list(
                    record["aliases"]
                ),

            "priority":
                record["priority"]

        }

    # ========================================================
    # Search Degrees
    # ========================================================

    def search_degrees(
        self,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Search education configuration using partial,
        case-insensitive matching.

        Searches:

            - Standard education name
            - Aliases
            - Priority text representation
        """

        normalized_query = self.normalize_text(
            query
        )

        if not normalized_query:

            return []

        results = []

        for record in (
            self._education_by_name.values()
        ):

            searchable_values = [

                record["name"],

                *record["aliases"]

            ]

            if record["priority"] is not None:

                searchable_values.append(
                    str(
                        record["priority"]
                    )
                )

            match_found = any(

                normalized_query
                in self.normalize_text(
                    value
                )

                for value
                in searchable_values

            )

            if match_found:

                results.append(

                    {

                        "name":
                            record["name"],

                        "aliases":
                            list(
                                record[
                                    "aliases"
                                ]
                            ),

                        "priority":
                            record[
                                "priority"
                            ]

                    }

                )

        return sorted(

            results,

            key=lambda item:
                item["name"].lower()

        )

    # ========================================================
    # DataFrame Access
    # ========================================================

    def get_dataframe(
        self
    ) -> pd.DataFrame:
        """
        Return a safe copy of the active Education DataFrame.

        Returning a copy prevents external modules from
        accidentally modifying repository state.
        """

        return self._dataframe.copy()

    # ========================================================
    # Refresh Repository
    # ========================================================

    def refresh(
        self
    ) -> None:
        """
        Reload RecruitOS_Configuration.xlsx and rebuild
        EducationRepository indexes.

        Use this method after configuration workbook changes.
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
        Print EducationRepository statistics.
        """

        print()

        print("=" * 60)

        print(
            "RecruitOS Enterprise Education Repository"
        )

        print("=" * 60)

        print(
            f"Total Degrees : "
            f"{self.total_degrees()}"
        )

        print("=" * 60)


# ============================================================
# Debug Execution
# ============================================================

if __name__ == "__main__":

    repository = (
        EducationRepository()
    )

    repository.display_summary()

    print()

    print("Configured Education")

    print("-" * 60)

    for degree in (
        repository.get_all_degrees()
    ):

        print(degree)