"""
============================================================
RecruitOS

Module      : Master Repository
Sprint      : 5.5.0.1
Version     : 1.0.0
Author      : Tamilvanan A

Purpose:
Loads RecruitOS_Configuration.xlsx only once,
caches it in memory, and provides centralized
access to all configuration sheets.

Every repository must use this class.

============================================================
"""

from pathlib import Path
from typing import Dict

import pandas as pd

from config.paths import CONFIGURATION_WORKBOOK
from config.sheet_names import ALL_SHEETS


class MasterRepository:
    """
    Enterprise Configuration Repository

    Singleton-style workbook loader.
    """

    _workbook_cache: Dict[str, pd.DataFrame] = {}

    _loaded = False

    # --------------------------------------------------

    @classmethod
    def load(cls):

        """
        Loads workbook once.
        """

        if cls._loaded:

            return

        workbook_path = Path(CONFIGURATION_WORKBOOK)

        if not workbook_path.exists():

            raise FileNotFoundError(

                f"\nConfiguration workbook not found\n"

                f"{workbook_path}\n"

                "Run:\n"

                "python tools/create_configuration_workbook.py"

            )

        excel = pd.ExcelFile(workbook_path)

        for sheet in excel.sheet_names:

            dataframe = pd.read_excel(

                workbook_path,

                sheet_name=sheet

            )

            cls._workbook_cache[sheet] = dataframe

        cls._loaded = True

    # --------------------------------------------------

    @classmethod
    def reload(cls):

        """
        Reload workbook from disk.
        """

        cls._workbook_cache = {}

        cls._loaded = False

        cls.load()

    # --------------------------------------------------

    @classmethod
    def get_sheet(cls, sheet_name: str) -> pd.DataFrame:

        """
        Returns requested sheet.
        """

        cls.load()

        if sheet_name not in cls._workbook_cache:

            raise ValueError(

                f"Sheet '{sheet_name}' not found."

            )

        return cls._workbook_cache[sheet_name].copy()

    # --------------------------------------------------

    @classmethod
    def has_sheet(cls, sheet_name: str) -> bool:

        cls.load()

        return sheet_name in cls._workbook_cache

    # --------------------------------------------------

    @classmethod
    def list_sheets(cls):

        cls.load()

        return list(cls._workbook_cache.keys())

    # --------------------------------------------------

    @classmethod
    def validate_workbook(cls):

        """
        Ensures all required sheets exist.
        """

        cls.load()

        missing = []

        for sheet in ALL_SHEETS:

            if sheet not in cls._workbook_cache:

                missing.append(sheet)

        if missing:

            raise ValueError(

                "Missing sheets:\n"

                + "\n".join(missing)

            )

        return True

    # --------------------------------------------------

    @classmethod
    def workbook_info(cls):

        cls.load()

        info = {}

        for sheet, dataframe in cls._workbook_cache.items():

            info[sheet] = {

                "Rows": len(dataframe),

                "Columns": len(dataframe.columns)

            }

        return info

    # --------------------------------------------------

    @classmethod
    def display_info(cls):

        info = cls.workbook_info()

        print("\nRecruitOS Configuration")

        print("--------------------------------------")

        for sheet, details in info.items():

            print(

                f"{sheet:<20}"

                f"Rows={details['Rows']:<5}"

                f"Cols={details['Columns']}"

            )

        print("--------------------------------------")