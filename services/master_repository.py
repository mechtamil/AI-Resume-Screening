"""Central cached access to ``RecruitOS_Configuration.xlsx``."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd

from config.paths import CONFIGURATION_WORKBOOK
from config.sheet_names import ALL_SHEETS, REQUIRED_COLUMNS


class MasterRepository:
    """Load and validate the central configuration workbook once per process."""

    _workbook_cache: Dict[str, pd.DataFrame] = {}
    _loaded = False

    @classmethod
    def load(cls) -> None:
        if cls._loaded:
            return

        workbook_path = Path(CONFIGURATION_WORKBOOK)
        if not workbook_path.exists():
            raise FileNotFoundError(
                "RecruitOS configuration workbook was not found:\n"
                f"{workbook_path}\n"
                "Create it from the project root with:\n"
                "python -m tools.create_configuration_workbook"
            )

        try:
            excel = pd.ExcelFile(workbook_path)
        except Exception as exc:  # pandas/openpyxl provides the detailed cause
            raise ValueError(
                f"Unable to open RecruitOS configuration workbook: {workbook_path}"
            ) from exc

        cls._workbook_cache = {
            sheet: pd.read_excel(workbook_path, sheet_name=sheet)
            for sheet in excel.sheet_names
        }
        cls._loaded = True

    @classmethod
    def reload(cls) -> None:
        cls._workbook_cache = {}
        cls._loaded = False
        cls.load()

    @classmethod
    def get_sheet(cls, sheet_name: str) -> pd.DataFrame:
        cls.load()
        if sheet_name not in cls._workbook_cache:
            raise ValueError(f"Configuration sheet '{sheet_name}' was not found.")
        return cls._workbook_cache[sheet_name].copy()

    @classmethod
    def has_sheet(cls, sheet_name: str) -> bool:
        cls.load()
        return sheet_name in cls._workbook_cache

    @classmethod
    def list_sheets(cls) -> list[str]:
        cls.load()
        return list(cls._workbook_cache.keys())

    @classmethod
    def validate_workbook(cls) -> bool:
        """Validate required sheets and required structural columns."""
        cls.load()

        missing_sheets = [sheet for sheet in ALL_SHEETS if sheet not in cls._workbook_cache]
        if missing_sheets:
            raise ValueError(
                "Missing required configuration sheet(s): " + ", ".join(missing_sheets)
            )

        schema_errors: list[str] = []
        for sheet_name, required_columns in REQUIRED_COLUMNS.items():
            dataframe = cls._workbook_cache[sheet_name]
            missing_columns = [
                column for column in required_columns if column not in dataframe.columns
            ]
            if missing_columns:
                schema_errors.append(
                    f"{sheet_name}: missing {', '.join(missing_columns)}"
                )

        if schema_errors:
            raise ValueError(
                "Invalid RecruitOS configuration workbook schema:\n- "
                + "\n- ".join(schema_errors)
            )
        return True

    @classmethod
    def workbook_info(cls) -> dict[str, dict[str, int]]:
        cls.load()
        return {
            sheet: {"Rows": len(dataframe), "Columns": len(dataframe.columns)}
            for sheet, dataframe in cls._workbook_cache.items()
        }

    @classmethod
    def display_info(cls) -> None:
        print("\nRecruitOS Configuration")
        print("-" * 60)
        for sheet, details in cls.workbook_info().items():
            print(f"{sheet:<20} Rows={details['Rows']:<5} Cols={details['Columns']}")
        print("-" * 60)
