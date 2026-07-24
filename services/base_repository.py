"""
============================================================
RecruitOS

Module      : Base Repository
Sprint      : 5.5.1
Version     : 1.0.0
Author       : Tamilvanan A

Purpose:
Provides common reusable functionality for all
repositories in RecruitOS.

Every repository should inherit from this class.

Examples:
    - SkillRepository
    - EducationRepository
    - CertificationRepository
    - CompanyRepository
    - ScoringRepository

============================================================
"""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List

import pandas as pd


class BaseRepository:
    """
    Enterprise Base Repository.

    Provides common DataFrame operations that can be reused
    across all repositories.
    """

    # ======================================================
    # Text Utilities
    # ======================================================

    @staticmethod
    def normalize_text(value: Any) -> str:
        """
        Normalizes text for comparisons.

        Example:
            " Python  "
            ↓
            "python"
        """

        if value is None:
            return ""

        return str(value).strip().lower()

    # ======================================================
    # List Utilities
    # ======================================================

    @staticmethod
    def remove_duplicates(items: List[Any]) -> List[Any]:
        """
        Removes duplicates while preserving order.
        """

        unique = []

        for item in items:

            if item not in unique:

                unique.append(item)

        return unique

    @classmethod
    def clean_list(cls, items: List[Any]) -> List[str]:
        """
        Cleans a list.

        • Removes None
        • Removes blanks
        • Removes duplicates
        """

        cleaned = []

        for item in items:

            text = cls.normalize_text(item)

            if text:

                cleaned.append(text)

        return cls.remove_duplicates(cleaned)

    # ======================================================
    # DataFrame Utilities
    # ======================================================

    @staticmethod
    def get_column(
        dataframe: pd.DataFrame,
        column_name: str
    ) -> List[Any]:
        """
        Returns one column as list.
        """

        if column_name not in dataframe.columns:

            return []

        return dataframe[column_name].dropna().tolist()

    @classmethod
    def get_clean_column(
        cls,
        dataframe: pd.DataFrame,
        column_name: str
    ) -> List[str]:
        """
        Returns normalized column values.
        """

        values = cls.get_column(
            dataframe,
            column_name
        )

        return cls.clean_list(values)

    # ======================================================
    # Search Utilities
    # ======================================================

    @classmethod
    def exists(
        cls,
        dataframe: pd.DataFrame,
        column_name: str,
        value: Any
    ) -> bool:
        """
        Checks whether a value exists.
        """

        value = cls.normalize_text(value)

        values = cls.get_clean_column(
            dataframe,
            column_name
        )

        return value in values

    @classmethod
    def search(
        cls,
        dataframe: pd.DataFrame,
        column_name: str,
        value: Any
    ) -> pd.DataFrame:
        """
        Returns matching rows.
        """

        value = cls.normalize_text(value)

        if column_name not in dataframe.columns:

            return pd.DataFrame()

        normalized = dataframe[column_name].fillna("").astype(str)

        mask = normalized.str.strip().str.lower() == value

        return dataframe.loc[mask]

    # ======================================================
    # Active Record Utilities
    # ======================================================

    @classmethod
    def filter_active(
        cls,
        dataframe: pd.DataFrame,
        active_column: str = "Active"
    ) -> pd.DataFrame:
        """
        Returns only active rows.

        Active values accepted:

            Yes
            YES
            yes
            True
            TRUE
            1
        """

        if active_column not in dataframe.columns:

            return dataframe

        normalized = (
            dataframe[active_column]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        return dataframe.loc[
            normalized.isin(
                [
                    "yes",
                    "true",
                    "1"
                ]
            )
        ]

    # ======================================================
    # Conversion Utilities
    # ======================================================

    @staticmethod
    def dataframe_to_list(
        dataframe: pd.DataFrame
    ) -> List[Dict]:
        """
        Converts DataFrame to list of dictionaries.
        """

        if dataframe.empty:

            return []

        return dataframe.to_dict(
            orient="records"
        )

    @staticmethod
    def dataframe_to_dict(
        dataframe: pd.DataFrame,
        key_column: str,
        value_column: str
    ) -> Dict[Any, Any]:
        """
        Converts two columns into a dictionary.

        Example

            Skill -> Category
        """

        if dataframe.empty:

            return {}

        if key_column not in dataframe.columns:

            return {}

        if value_column not in dataframe.columns:

            return {}

        return dict(
            zip(
                dataframe[key_column],
                dataframe[value_column]
            )
        )

    # ======================================================
    # Statistics
    # ======================================================

    @staticmethod
    def total_records(
        dataframe: pd.DataFrame
    ) -> int:
        """
        Returns total records.
        """

        return len(dataframe.index)

    @staticmethod
    def total_columns(
        dataframe: pd.DataFrame
    ) -> int:
        """
        Returns total columns.
        """

        return len(dataframe.columns)

    @staticmethod
    def is_empty(
        dataframe: pd.DataFrame
    ) -> bool:
        """
        Checks whether dataframe is empty.
        """

        return dataframe.empty

    # ======================================================
    # Display
    # ======================================================

    @classmethod
    def display_summary(
        cls,
        dataframe: pd.DataFrame,
        title: str = "Repository"
    ):
        """
        Prints repository summary.
        """

        print()

        print("=" * 60)

        print(title)

        print("=" * 60)

        print(f"Rows     : {cls.total_records(dataframe)}")

        print(f"Columns  : {cls.total_columns(dataframe)}")

        print("=" * 60)