"""Read an optional user-provided skill requirement list."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from services.skill_repository import SkillRepository


class SkillListService:
    CANDIDATE_COLUMNS = ("Skill", "Skill Name", "Mandatory Skill", "Mandatory Skills", "Required Skill")

    @classmethod
    def read_skills(cls, file_path: str | Path) -> list[str]:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Skill list not found: {path}")
        extension = path.suffix.lower()
        if extension == ".xlsx":
            frame = pd.read_excel(path)
            values = cls._from_dataframe(frame)
        elif extension == ".csv":
            frame = pd.read_csv(path)
            values = cls._from_dataframe(frame)
        elif extension == ".txt":
            values = [part.strip() for line in path.read_text(encoding="utf-8").splitlines() for part in line.replace(";", ",").split(",")]
        else:
            raise ValueError(f"Unsupported skill-list file type: {extension}")
        return cls._standardize(values)

    @classmethod
    def _from_dataframe(cls, frame: pd.DataFrame) -> list[str]:
        if frame.empty:
            return []
        column = next((name for name in cls.CANDIDATE_COLUMNS if name in frame.columns), frame.columns[0])
        return [str(value).strip() for value in frame[column].dropna().tolist()]

    @staticmethod
    def _standardize(values: list[str]) -> list[str]:
        repo = SkillRepository()
        output: list[str] = []
        seen: set[str] = set()
        for value in values:
            cleaned = str(value or "").strip()
            if not cleaned:
                continue
            standard = repo.find_standard_skill(cleaned) or cleaned
            key = standard.casefold()
            if key not in seen:
                seen.add(key)
                output.append(standard)
        return output
