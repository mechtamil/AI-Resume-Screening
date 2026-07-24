"""Read active location master data from the central configuration workbook."""
from __future__ import annotations

import pandas as pd

from config.sheet_names import LOCATIONS
from services.base_repository import BaseRepository
from services.master_repository import MasterRepository


class LocationRepository(BaseRepository):
    SHEET_NAME = LOCATIONS

    def __init__(self) -> None:
        dataframe = MasterRepository.get_sheet(self.SHEET_NAME).copy().fillna("")
        self._dataframe = self.filter_active(dataframe, "Active").reset_index(drop=True)

    def get_search_values(self) -> list[str]:
        """Return unique configured city/state/country values, longest first."""
        values: dict[str, str] = {}
        for column in ("City", "State", "Country"):
            if column not in self._dataframe.columns:
                continue
            for value in self._dataframe[column].tolist():
                cleaned = str(value).strip()
                key = self.normalize_text(cleaned)
                if key:
                    values.setdefault(key, cleaned)
        return sorted(values.values(), key=len, reverse=True)

    def get_dataframe(self) -> pd.DataFrame:
        return self._dataframe.copy()
