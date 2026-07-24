"""
============================================================
RecruitOS

Module      : Enterprise Skill Repository
Sprint      : 5.5.2
Version     : 3.0.0
Author      : Tamilvanan A

Purpose:
Provides centralized access to skill master data stored in
the "Skills" sheet of RecruitOS_Configuration.xlsx.

Architecture:

RecruitOS_Configuration.xlsx
        ↓
MasterRepository
        ↓
BaseRepository
        ↓
SkillRepository
        ↓
Resume Parser
JD Parser
Skill Extractor
Matching Engine
Analytics
AI Services

Important:
This repository does NOT read Excel directly.

All workbook access must go through MasterRepository.

============================================================
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

import pandas as pd

from config.sheet_names import SKILLS
from services.base_repository import BaseRepository
from services.master_repository import MasterRepository


class SkillRepository(BaseRepository):
    """
    Enterprise Skill Repository.

    Provides standardized skill lookup, normalization,
    synonym handling, category lookup, and search.

    Backward compatibility is maintained for existing
    RecruitOS modules using:

        get_all_skills()
        get_skill_names()
        is_valid_skill()
        get_skill_synonyms()
        find_standard_skill()
        get_category()
        total_skills()
    """

    # ========================================================
    # Sheet Configuration
    # ========================================================

    SHEET_NAME = SKILLS

    SKILL_COLUMN = "Skill"

    CATEGORY_COLUMN = "Category"

    SUB_CATEGORY_COLUMN = "Sub Category"

    SYNONYMS_COLUMN = "Synonyms"

    ACTIVE_COLUMN = "Active"

    # ========================================================
    # Initialization
    # ========================================================

    def __init__(self):
        """
        Initialize the repository from MasterRepository.
        """

        self._dataframe = pd.DataFrame()

        self._skills_by_name: Dict[str, Dict] = {}

        self._alias_to_standard: Dict[str, str] = {}

        self.load_repository()

    # ========================================================
    # Repository Loading
    # ========================================================

    def load_repository(self) -> None:
        """
        Load active skill records from MasterRepository.

        The workbook itself is loaded and cached by
        MasterRepository.

        SkillRepository only consumes the Skills sheet.
        """

        dataframe = MasterRepository.get_sheet(
            self.SHEET_NAME
        )

        self._validate_structure(dataframe)

        dataframe = dataframe.copy()

        dataframe.fillna(
            "",
            inplace=True
        )

        # Filter inactive records when Active column exists.
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
    # Validation
    # ========================================================

    def _validate_structure(
        self,
        dataframe: pd.DataFrame
    ) -> None:
        """
        Validate required Skills sheet columns.

        Skill is the only mandatory column.

        Category, Sub Category, Synonyms and Active are
        optional to maintain compatibility with simpler
        configuration workbooks.
        """

        if dataframe is None:

            raise ValueError(
                "Skills sheet could not be loaded."
            )

        if self.SKILL_COLUMN not in dataframe.columns:

            raise ValueError(
                "Invalid Skills sheet. "
                f"Required column missing: "
                f"'{self.SKILL_COLUMN}'"
            )

    # ========================================================
    # Index Building
    # ========================================================

    def _build_indexes(self) -> None:
        """
        Build fast in-memory lookup indexes.

        Indexes:

        _skills_by_name
            normalized standard skill -> details

        _alias_to_standard
            normalized synonym/alias -> standard skill
        """

        self._skills_by_name = {}

        self._alias_to_standard = {}

        for _, row in self._dataframe.iterrows():

            skill_name = str(
                row.get(
                    self.SKILL_COLUMN,
                    ""
                )
            ).strip()

            if not skill_name:

                continue

            normalized_skill = self.normalize_text(
                skill_name
            )

            category = str(
                row.get(
                    self.CATEGORY_COLUMN,
                    ""
                )
            ).strip()

            sub_category = str(
                row.get(
                    self.SUB_CATEGORY_COLUMN,
                    ""
                )
            ).strip()

            synonyms_raw = str(
                row.get(
                    self.SYNONYMS_COLUMN,
                    ""
                )
            ).strip()

            synonyms = self._parse_synonyms(
                synonyms_raw
            )

            record = {

                "name": skill_name,

                "category": category,

                "sub_category": sub_category,

                "synonyms": synonyms

            }

            self._skills_by_name[
                normalized_skill
            ] = record

            # Standard skill itself is also a valid alias.

            self._alias_to_standard[
                normalized_skill
            ] = skill_name

            # Register synonyms.

            for synonym in synonyms:

                normalized_synonym = (
                    self.normalize_text(
                        synonym
                    )
                )

                if normalized_synonym:

                    self._alias_to_standard[
                        normalized_synonym
                    ] = skill_name

    # ========================================================
    # Synonym Parsing
    # ========================================================

    @classmethod
    def _parse_synonyms(
        cls,
        value: str
    ) -> List[str]:
        """
        Parse synonyms from Excel.

        Supports common separators:

            ;
            ,
            |

        Examples:

            Python3;Py
            Python3,Py
            Python3|Py

        All are converted into:

            ["Python3", "Py"]
        """

        if not value:

            return []

        parts = re.split(
            r"[;,|]",
            str(value)
        )

        synonyms = []

        seen = set()

        for part in parts:

            synonym = part.strip()

            normalized = cls.normalize_text(
                synonym
            )

            if (
                normalized
                and normalized not in seen
            ):

                seen.add(normalized)

                synonyms.append(
                    synonym
                )

        return synonyms

    # ========================================================
    # Public Repository API
    # ========================================================

    def get_all_skills(self) -> List[str]:
        """
        Return all active standardized skill names.
        """

        skills = [

            record["name"]

            for record
            in self._skills_by_name.values()

        ]

        return sorted(
            skills,
            key=str.lower
        )

    # ========================================================

    def get_skill_names(self) -> List[str]:
        """
        Backward-compatible alias for get_all_skills().
        """

        return self.get_all_skills()

    # ========================================================

    def total_skills(self) -> int:
        """
        Return number of active standard skills.
        """

        return len(
            self._skills_by_name
        )

    # ========================================================

    def find_standard_skill(
        self,
        value: str
    ) -> Optional[str]:
        """
        Resolve a skill or synonym to its standardized name.

        Example:

            "Python3"
                ↓
            "Python"

        Returns None when no match exists.
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

    def normalize_skill(
        self,
        value: str
    ) -> Optional[str]:
        """
        Normalize a skill or synonym.

        This is the preferred enterprise API.

        Example:

            normalize_skill(" python3 ")

        Returns:

            "Python"
        """

        return self.find_standard_skill(
            value
        )

    # ========================================================

    def is_valid_skill(
        self,
        skill: str
    ) -> bool:
        """
        Check whether a standard skill or synonym exists.

        Synonyms are treated as valid skill references.
        """

        return (
            self.find_standard_skill(skill)
            is not None
        )

    # ========================================================

    def get_skill_synonyms(
        self,
        skill: str
    ) -> List[str]:
        """
        Return synonyms for a standardized skill.

        The input may itself be a synonym.
        """

        standard = self.find_standard_skill(
            skill
        )

        if not standard:

            return []

        normalized_standard = (
            self.normalize_text(
                standard
            )
        )

        record = self._skills_by_name.get(
            normalized_standard
        )

        if not record:

            return []

        return list(
            record["synonyms"]
        )

    # ========================================================

    def get_category(
        self,
        skill: str
    ) -> Optional[str]:
        """
        Return category of a skill.

        The input may be either:

            Standard skill
            Synonym
        """

        details = self.get_skill_details(
            skill
        )

        if not details:

            return None

        return details["category"]

    # ========================================================

    def get_sub_category(
        self,
        skill: str
    ) -> Optional[str]:
        """
        Return sub-category of a skill.
        """

        details = self.get_skill_details(
            skill
        )

        if not details:

            return None

        return details["sub_category"]

    # ========================================================

    def get_skill_details(
        self,
        skill: str
    ) -> Optional[Dict]:
        """
        Return complete skill metadata.

        Example:

        {
            "name": "Python",
            "category": "Programming",
            "sub_category": "Backend",
            "synonyms": ["Python3", "Py"]
        }
        """

        standard = self.find_standard_skill(
            skill
        )

        if not standard:

            return None

        normalized_standard = (
            self.normalize_text(
                standard
            )
        )

        record = self._skills_by_name.get(
            normalized_standard
        )

        if not record:

            return None

        return {

            "name": record["name"],

            "category": record[
                "category"
            ],

            "sub_category": record[
                "sub_category"
            ],

            "synonyms": list(
                record["synonyms"]
            )

        }

    # ========================================================
    # Category APIs
    # ========================================================

    def get_skill_categories(
        self
    ) -> List[str]:
        """
        Return unique active skill categories.
        """

        categories = []

        seen = set()

        for record in (
            self._skills_by_name.values()
        ):

            category = record[
                "category"
            ].strip()

            normalized = (
                self.normalize_text(
                    category
                )
            )

            if (
                normalized
                and normalized not in seen
            ):

                seen.add(
                    normalized
                )

                categories.append(
                    category
                )

        return sorted(
            categories,
            key=str.lower
        )

    # ========================================================

    def get_skills_by_category(
        self,
        category: str
    ) -> List[str]:
        """
        Return skills belonging to a category.
        """

        normalized_category = (
            self.normalize_text(
                category
            )
        )

        if not normalized_category:

            return []

        skills = []

        for record in (
            self._skills_by_name.values()
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

                skills.append(
                    record["name"]
                )

        return sorted(
            skills,
            key=str.lower
        )

    # ========================================================
    # Search
    # ========================================================

    def search_skills(
        self,
        query: str
    ) -> List[Dict]:
        """
        Search skills using:

            Skill name
            Category
            Sub-category
            Synonyms

        Search is case-insensitive and supports
        partial text matching.
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
            self._skills_by_name.values()
        ):

            searchable_values = [

                record["name"],

                record["category"],

                record["sub_category"],

                *record["synonyms"]

            ]

            match_found = any(

                normalized_query
                in self.normalize_text(value)

                for value
                in searchable_values

            )

            if match_found:

                results.append(

                    {

                        "name":
                            record["name"],

                        "category":
                            record[
                                "category"
                            ],

                        "sub_category":
                            record[
                                "sub_category"
                            ],

                        "synonyms":
                            list(
                                record[
                                    "synonyms"
                                ]
                            )

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
        Return a safe copy of the active Skills DataFrame.

        External modules cannot modify the internal
        repository DataFrame directly.
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
        the SkillRepository indexes.

        Use this after the configuration workbook has
        been modified.
        """

        MasterRepository.reload()

        self.load_repository()

    # ========================================================
    # Display
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
            "RecruitOS Enterprise Skill Repository"
        )

        print("=" * 60)

        print(
            f"Total Skills     : "
            f"{self.total_skills()}"
        )

        print(
            f"Total Categories : "
            f"{len(self.get_skill_categories())}"
        )

        print("=" * 60)


# ============================================================
# Debug Execution
# ============================================================

if __name__ == "__main__":

    repository = SkillRepository()

    repository.display_summary()

    print()

    print("Skills")

    print("-" * 60)

    for skill in (
        repository.get_all_skills()
    ):

        print(skill)