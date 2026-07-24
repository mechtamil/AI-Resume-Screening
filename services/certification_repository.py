"""
============================================================
RecruitOS

Module      : Enterprise Certification Repository
Sprint      : 5.5.4
Version     : 2.0.0
Author      : Tamilvanan A

Purpose:
Provides centralized access to certification master data
stored in the "Certifications" sheet of
RecruitOS_Configuration.xlsx.

Architecture:

RecruitOS_Configuration.xlsx
        ↓
MasterRepository
        ↓
BaseRepository
        ↓
CertificationRepository
        ↓
Resume Parser
Certification Extractor
Certification Matcher
Analytics
AI Services

Important:
- This repository does NOT read Excel directly.
- MasterRepository is the only workbook access layer.
- No certification business/master data is hardcoded here.

============================================================
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import pandas as pd

from config.sheet_names import CERTIFICATIONS
from services.base_repository import BaseRepository
from services.master_repository import MasterRepository


class CertificationRepository(BaseRepository):
    """
    Enterprise Certification Repository.

    Responsibilities:

        - Load certification configuration
        - Return active certifications
        - Resolve aliases to standard certification names
        - Validate certifications
        - Return certification categories
        - Search certifications
        - Provide metadata
        - Refresh repository after workbook changes

    Example:

        repository = CertificationRepository()

        repository.get_all_certifications()

        repository.normalize_certification("Configured Alias")

        repository.is_valid_certification("Certification Name")

        repository.get_category("Certification Name")
    """

    # ========================================================
    # Sheet Configuration
    # ========================================================

    SHEET_NAME = CERTIFICATIONS

    CERTIFICATION_COLUMN = "Certification"

    ALIAS_COLUMN = "Alias"

    CATEGORY_COLUMN = "Category"

    ACTIVE_COLUMN = "Active"

    # ========================================================
    # Initialization
    # ========================================================

    def __init__(self) -> None:
        """
        Initialize CertificationRepository.
        """

        self._dataframe = pd.DataFrame()

        self._certifications_by_name: Dict[
            str,
            Dict[str, Any]
        ] = {}

        self._alias_to_standard: Dict[
            str,
            str
        ] = {}

        self.load_repository()

    # ========================================================
    # Repository Loading
    # ========================================================

    def load_repository(self) -> None:
        """
        Load certification records through MasterRepository.

        MasterRepository handles:

            - Workbook loading
            - Workbook caching
            - Sheet access

        CertificationRepository handles only certification
        domain logic.
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

        self._build_indexes()

    # ========================================================
    # Structure Validation
    # ========================================================

    def _validate_structure(
        self,
        dataframe: pd.DataFrame
    ) -> None:
        """
        Validate Certifications sheet structure.

        Required column:

            Certification

        Optional columns:

            Alias
            Category
            Active

        Only Certification is mandatory so the repository
        remains compatible with both simple and extended
        configuration workbooks.
        """

        if dataframe is None:

            raise ValueError(
                "Certifications sheet could not be loaded."
            )

        if (
            self.CERTIFICATION_COLUMN
            not in dataframe.columns
        ):

            raise ValueError(
                "Invalid Certifications sheet. "
                "Required column missing: "
                f"'{self.CERTIFICATION_COLUMN}'"
            )

    # ========================================================
    # Build Repository Indexes
    # ========================================================

    def _build_indexes(self) -> None:
        """
        Build fast in-memory indexes.

        Index 1:

            normalized certification name
                ↓
            certification metadata

        Index 2:

            normalized certification name or alias
                ↓
            standard certification name
        """

        self._certifications_by_name = {}

        self._alias_to_standard = {}

        for _, row in self._dataframe.iterrows():

            certification_name = str(
                row.get(
                    self.CERTIFICATION_COLUMN,
                    ""
                )
            ).strip()

            if not certification_name:

                continue

            normalized_name = self.normalize_text(
                certification_name
            )

            # Prevent duplicate standard certification names.

            if (
                normalized_name
                in self._certifications_by_name
            ):

                raise ValueError(
                    "Duplicate certification detected in "
                    "RecruitOS_Configuration.xlsx: "
                    f"'{certification_name}'. "
                    "Each active Certification value must "
                    "be unique."
                )

            aliases = self._parse_aliases(
                row.get(
                    self.ALIAS_COLUMN,
                    ""
                )
            )

            category = str(
                row.get(
                    self.CATEGORY_COLUMN,
                    ""
                )
            ).strip()

            record = {

                "name":
                    certification_name,

                "aliases":
                    aliases,

                "category":
                    category

            }

            self._certifications_by_name[
                normalized_name
            ] = record

            # Standard name itself is always valid.

            self._register_alias(
                alias=certification_name,
                standard_name=certification_name
            )

            # Register configured aliases.

            for alias in aliases:

                self._register_alias(
                    alias=alias,
                    standard_name=certification_name
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
        Register a certification alias.

        Ambiguous aliases are rejected.

        Example of invalid configuration:

            Certification A -> ABC
            Certification B -> ABC

        RecruitOS cannot reliably normalize "ABC" when it
        points to two certifications, so configuration must
        be corrected instead of guessing.
        """

        normalized_alias = self.normalize_text(
            alias
        )

        if not normalized_alias:

            return

        existing_standard = (
            self._alias_to_standard.get(
                normalized_alias
            )
        )

        if (
            existing_standard
            and self.normalize_text(
                existing_standard
            )
            != self.normalize_text(
                standard_name
            )
        ):

            raise ValueError(
                "Ambiguous certification alias detected: "
                f"'{alias}'. "
                f"It is mapped to both "
                f"'{existing_standard}' and "
                f"'{standard_name}'. "
                "Please correct the Certifications sheet in "
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
        Parse certification aliases from Excel.

        Supported separators:

            ;
            ,
            |

        Example:

            Alias1;Alias2
            Alias1,Alias2
            Alias1|Alias2

        All formats are supported.

        Duplicate aliases are removed while preserving the
        first configured spelling.
        """

        if value is None:

            return []

        text = str(
            value
        ).strip()

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

            normalized_alias = (
                cls.normalize_text(
                    alias
                )
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
    # Get All Certifications
    # ========================================================

    def get_all_certifications(
        self
    ) -> List[str]:
        """
        Return all active standardized certification names.
        """

        certifications = [

            record["name"]

            for record
            in self._certifications_by_name.values()

        ]

        return sorted(
            certifications,
            key=str.lower
        )

    # ========================================================
    # Compatibility API
    # ========================================================

    def get_all(
        self
    ) -> List[str]:
        """
        Backward-compatible shorthand.

        Existing RecruitOS modules that call:

            repository.get_all()

        will continue to work.
        """

        return self.get_all_certifications()

    # ========================================================

    def get_certification_names(
        self
    ) -> List[str]:
        """
        Friendly alias for get_all_certifications().
        """

        return self.get_all_certifications()

    # ========================================================
    # Total Certifications
    # ========================================================

    def total_certifications(
        self
    ) -> int:
        """
        Return total active configured certifications.
        """

        return len(
            self._certifications_by_name
        )

    # ========================================================
    # Find Standard Certification
    # ========================================================

    def find_standard_certification(
        self,
        value: str
    ) -> Optional[str]:
        """
        Resolve either:

            - Standard certification name
            - Configured alias

        to the configured standard certification name.

        Unknown values return None.
        """

        normalized_value = (
            self.normalize_text(
                value
            )
        )

        if not normalized_value:

            return None

        return self._alias_to_standard.get(
            normalized_value
        )

    # ========================================================
    # Compatibility Method
    # ========================================================

    def get_standard_name(
        self,
        value: str
    ) -> Optional[str]:
        """
        Backward-compatible API for older certification
        extractor implementations.
        """

        return self.find_standard_certification(
            value
        )

    # ========================================================
    # Normalize Certification
    # ========================================================

    def normalize_certification(
        self,
        value: str
    ) -> Optional[str]:
        """
        Preferred enterprise normalization API.

        Example:

            Configured standard:
                Example Professional Certification

            Configured alias:
                EPC

            Input:
                EPC

            Returns:
                Example Professional Certification

        Actual values always come from Excel.
        """

        return self.find_standard_certification(
            value
        )

    # ========================================================
    # Additional Compatibility Alias
    # ========================================================

    def normalize(
        self,
        value: str
    ) -> Optional[str]:
        """
        Compatibility shorthand for normalize_certification().
        """

        return self.normalize_certification(
            value
        )

    # ========================================================
    # Validation
    # ========================================================

    def is_valid_certification(
        self,
        value: str
    ) -> bool:
        """
        Check whether a certification name or alias exists.
        """

        return (
            self.find_standard_certification(
                value
            )
            is not None
        )

    # ========================================================

    def is_valid(
        self,
        value: str
    ) -> bool:
        """
        Backward-compatible shorthand for
        is_valid_certification().
        """

        return self.is_valid_certification(
            value
        )

    # ========================================================
    # Find Alias
    # ========================================================

    def find_alias(
        self,
        value: str
    ) -> Optional[str]:
        """
        Resolve an alias to its standard certification.

        Standard certification names are also accepted.

        This method is intentionally equivalent to the
        normalization API because both standard names and
        aliases are valid repository lookup values.
        """

        return self.find_standard_certification(
            value
        )

    # ========================================================
    # Get Aliases
    # ========================================================

    def get_aliases(
        self,
        value: str
    ) -> List[str]:
        """
        Return configured aliases for a certification.

        Input may be:

            - Standard certification name
            - Alias
        """

        details = (
            self.get_certification_details(
                value
            )
        )

        if not details:

            return []

        return list(
            details["aliases"]
        )

    # ========================================================
    # Get Category
    # ========================================================

    def get_category(
        self,
        value: str
    ) -> Optional[str]:
        """
        Return certification category.

        Input may be either the standard name or an alias.
        """

        details = (
            self.get_certification_details(
                value
            )
        )

        if not details:

            return None

        return details[
            "category"
        ]

    # ========================================================
    # Certification Details
    # ========================================================

    def get_certification_details(
        self,
        value: str
    ) -> Optional[Dict[str, Any]]:
        """
        Return complete certification metadata.

        Example structure:

        {
            "name": "<configured certification>",
            "aliases": ["<alias 1>", "<alias 2>"],
            "category": "<configured category>"
        }
        """

        standard_name = (
            self.find_standard_certification(
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
            self._certifications_by_name.get(
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

            "category":
                record["category"]

        }

    # ========================================================
    # Categories
    # ========================================================

    def get_categories(
        self
    ) -> List[str]:
        """
        Return unique configured certification categories.
        """

        categories = []

        seen = set()

        for record in (
            self._certifications_by_name.values()
        ):

            category = str(
                record["category"]
            ).strip()

            normalized_category = (
                self.normalize_text(
                    category
                )
            )

            if (
                normalized_category
                and normalized_category not in seen
            ):

                seen.add(
                    normalized_category
                )

                categories.append(
                    category
                )

        return sorted(
            categories,
            key=str.lower
        )

    # ========================================================
    # Certifications By Category
    # ========================================================

    def get_certifications_by_category(
        self,
        category: str
    ) -> List[str]:
        """
        Return certifications belonging to a configured
        category.
        """

        normalized_category = (
            self.normalize_text(
                category
            )
        )

        if not normalized_category:

            return []

        certifications = []

        for record in (
            self._certifications_by_name.values()
        ):

            record_category = (
                self.normalize_text(
                    record["category"]
                )
            )

            if (
                record_category
                == normalized_category
            ):

                certifications.append(
                    record["name"]
                )

        return sorted(
            certifications,
            key=str.lower
        )

    # ========================================================
    # Search
    # ========================================================

    def search_certifications(
        self,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Search certification records.

        Search covers:

            - Certification name
            - Alias
            - Category

        Matching is:

            - Case-insensitive
            - Partial text
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
            self._certifications_by_name.values()
        ):

            searchable_values = [

                record["name"],

                record["category"],

                *record["aliases"]

            ]

            matched = any(

                normalized_query
                in self.normalize_text(
                    item
                )

                for item
                in searchable_values

            )

            if matched:

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

                        "category":
                            record[
                                "category"
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
        Return a safe copy of the active Certifications
        DataFrame.

        External modules cannot directly modify repository
        internal state.
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
        CertificationRepository indexes.

        Use after the workbook has been modified.
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
        Print CertificationRepository statistics.
        """

        print()

        print("=" * 60)

        print(
            "RecruitOS Enterprise Certification Repository"
        )

        print("=" * 60)

        print(
            f"Total Certifications : "
            f"{self.total_certifications()}"
        )

        print(
            f"Total Categories      : "
            f"{len(self.get_categories())}"
        )

        print("=" * 60)


# ============================================================
# Debug Execution
# ============================================================

if __name__ == "__main__":

    repository = (
        CertificationRepository()
    )

    repository.display_summary()

    print()

    print(
        "Configured Certifications"
    )

    print("-" * 60)

    for certification in (
        repository.get_all_certifications()
    ):

        print(
            certification
        )