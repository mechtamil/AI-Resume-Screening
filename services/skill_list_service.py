"""Read optional supplemental skill requirements from common document formats."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from services.document_manager import DocumentManager
from services.skill_repository import SkillRepository


class SkillListService:
    """Normalize mandatory and preferred supplemental skill requirements."""

    CANDIDATE_COLUMNS = (
        "Skill",
        "Skill Name",
        "Mandatory Skill",
        "Mandatory Skills",
        "Required Skill",
    )
    TYPE_COLUMNS = ("Requirement Type", "Type", "Requirement", "Category")

    @classmethod
    def read_requirements(cls, file_path: str | Path) -> dict[str, list[str]]:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Skill list not found: {path}")

        extension = path.suffix.casefold()
        if extension in {".xlsx", ".xls", ".csv"}:
            mandatory, preferred = cls._from_tabular(path)
        else:
            document = DocumentManager.read_document(path)
            values = cls._split_text(str(document.get("text") or ""))
            mandatory, preferred = values, []

        return {
            "mandatory": cls._standardize(mandatory),
            "preferred": cls._standardize(preferred),
        }

    @classmethod
    def read_skills(cls, file_path: str | Path) -> list[str]:
        """Backward-compatible combined skill list."""
        requirements = cls.read_requirements(file_path)
        return cls._dedupe(requirements["mandatory"] + requirements["preferred"])

    @classmethod
    def _from_tabular(cls, path: Path) -> tuple[list[str], list[str]]:
        if path.suffix.casefold() == ".csv":
            frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        else:
            sheets = pd.read_excel(
                path,
                sheet_name=None,
                dtype=str,
                keep_default_na=False,
            )
            frame = next(
                (value for key, value in sheets.items() if key.casefold() == "skills"),
                next(iter(sheets.values()), pd.DataFrame()),
            )

        if frame.empty:
            return [], []

        columns = {str(column).strip().casefold(): column for column in frame.columns}
        skill_column = next(
            (columns[name.casefold()] for name in cls.CANDIDATE_COLUMNS if name.casefold() in columns),
            frame.columns[0],
        )
        type_column = next(
            (columns[name.casefold()] for name in cls.TYPE_COLUMNS if name.casefold() in columns),
            None,
        )

        mandatory: list[str] = []
        preferred: list[str] = []
        for _, row in frame.iterrows():
            skill = str(row.get(skill_column) or "").strip()
            if not skill:
                continue
            requirement_type = str(row.get(type_column) or "Mandatory").strip().casefold()
            if requirement_type.startswith("pref") or requirement_type.startswith("nice"):
                preferred.append(skill)
            else:
                mandatory.append(skill)
        return mandatory, preferred

    @staticmethod
    def _split_text(text: str) -> list[str]:
        values: list[str] = []
        for line in (text or "").splitlines():
            cleaned_line = line.strip()
            if not cleaned_line or cleaned_line.casefold().startswith("sheet:"):
                continue
            for part in cleaned_line.replace(";", ",").replace("|", ",").split(","):
                cleaned = part.strip(" \t-•")
                if cleaned:
                    values.append(cleaned)
        return values

    @staticmethod
    def _standardize(values: list[str]) -> list[str]:
        repository = SkillRepository()
        output: list[str] = []
        for value in values:
            cleaned = str(value or "").strip()
            if cleaned:
                output.append(repository.find_standard_skill(cleaned) or cleaned)
        return SkillListService._dedupe(output)

    @staticmethod
    def _dedupe(values: list[str]) -> list[str]:
        output: list[str] = []
        seen: set[str] = set()
        for value in values:
            key = str(value or "").strip().casefold()
            if key and key not in seen:
                seen.add(key)
                output.append(str(value).strip())
        return output
