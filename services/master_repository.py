"""Context-aware cached access to RecruitOS configuration workbooks."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from threading import RLock
from typing import Dict

import pandas as pd

from config.paths import CONFIGURATION_WORKBOOK
from config.sheet_names import ALL_SHEETS, REQUIRED_COLUMNS
from services.configuration_context import ConfigurationContext


class MasterRepository:
    """Load configuration workbooks with cache isolation by resolved file identity.

    The active workbook is selected from :class:`ConfigurationContext`. When no
    scoped configuration is active, the source-controlled system-default workbook
    is used. Cache entries are keyed by absolute path, file size and modification
    time so one tenant cannot reuse another tenant's workbook data.
    """

    _cache: Dict[tuple[str, int, int], Dict[str, pd.DataFrame]] = {}
    _lock = RLock()

    @classmethod
    def active_workbook_path(cls, workbook_path: str | Path | None = None) -> Path:
        if workbook_path is not None:
            return Path(workbook_path).expanduser().resolve()
        selection = ConfigurationContext.current()
        if selection is not None:
            return Path(selection.workbook_path).expanduser().resolve()
        return Path(CONFIGURATION_WORKBOOK).expanduser().resolve()

    @classmethod
    def _cache_key(cls, path: Path) -> tuple[str, int, int]:
        stat = path.stat()
        return (str(path), int(stat.st_size), int(stat.st_mtime_ns))

    @classmethod
    def load(
        cls,
        workbook_path: str | Path | None = None,
    ) -> Dict[str, pd.DataFrame]:
        path = cls.active_workbook_path(workbook_path)
        if not path.is_file():
            raise FileNotFoundError(
                "RecruitOS configuration workbook was not found:\n"
                f"{path}\n"
                "Create the system default from the project root with:\n"
                "python -m tools.create_configuration_workbook"
            )

        key = cls._cache_key(path)
        with cls._lock:
            cached = cls._cache.get(key)
            if cached is not None:
                return cached

            try:
                with pd.ExcelFile(path) as excel:
                    loaded = {
                        sheet: pd.read_excel(excel, sheet_name=sheet)
                        for sheet in excel.sheet_names
                    }
            except Exception as exc:
                raise ValueError(
                    f"Unable to open RecruitOS configuration workbook: {path}"
                ) from exc

            # Drop stale cache entries for the same path before registering the
            # new file identity.
            for existing in [item for item in cls._cache if item[0] == str(path)]:
                cls._cache.pop(existing, None)
            cls._cache[key] = loaded
            return loaded

    @classmethod
    def reload(cls, workbook_path: str | Path | None = None) -> None:
        path = cls.active_workbook_path(workbook_path)
        with cls._lock:
            for key in [item for item in cls._cache if item[0] == str(path)]:
                cls._cache.pop(key, None)
        cls.load(path)

    @classmethod
    def clear_cache(cls) -> None:
        with cls._lock:
            cls._cache.clear()

    @classmethod
    def get_sheet(
        cls,
        sheet_name: str,
        workbook_path: str | Path | None = None,
    ) -> pd.DataFrame:
        workbook = cls.load(workbook_path)
        if sheet_name not in workbook:
            raise ValueError(f"Configuration sheet '{sheet_name}' was not found.")
        return workbook[sheet_name].copy()

    @classmethod
    def has_sheet(
        cls,
        sheet_name: str,
        workbook_path: str | Path | None = None,
    ) -> bool:
        return sheet_name in cls.load(workbook_path)

    @classmethod
    def list_sheets(cls, workbook_path: str | Path | None = None) -> list[str]:
        return list(cls.load(workbook_path).keys())

    @classmethod
    def validate_workbook(cls, workbook_path: str | Path | None = None) -> bool:
        workbook = cls.load(workbook_path)
        missing_sheets = [sheet for sheet in ALL_SHEETS if sheet not in workbook]
        if missing_sheets:
            raise ValueError(
                "Missing required configuration sheet(s): " + ", ".join(missing_sheets)
            )

        schema_errors: list[str] = []
        for sheet_name, required_columns in REQUIRED_COLUMNS.items():
            dataframe = workbook[sheet_name]
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
    def workbook_info(
        cls,
        workbook_path: str | Path | None = None,
    ) -> dict[str, dict[str, int]]:
        return {
            sheet: {"Rows": len(dataframe), "Columns": len(dataframe.columns)}
            for sheet, dataframe in cls.load(workbook_path).items()
        }

    @classmethod
    def workbook_sha256(cls, workbook_path: str | Path | None = None) -> str:
        path = cls.active_workbook_path(workbook_path)
        digest = sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @classmethod
    def display_info(cls, workbook_path: str | Path | None = None) -> None:
        print("\nRecruitOS Configuration")
        print("-" * 60)
        for sheet, details in cls.workbook_info(workbook_path).items():
            print(f"{sheet:<20} Rows={details['Rows']:<5} Cols={details['Columns']}")
        print("-" * 60)
