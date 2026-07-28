"""Create a safe, empty RecruitOS configuration workbook template.

Run from the project root:
    python -m tools.create_configuration_workbook

The generator creates structure only; it does not hardcode business master data,
scoring weights, recommendation thresholds, or recruitment requirements.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Support both `python -m tools.create_configuration_workbook` and direct execution.
if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import argparse
import shutil
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from config.paths import CONFIGURATION_WORKBOOK, MASTER_DATA_DIR
from config.sheet_names import ALL_SHEETS, REQUIRED_COLUMNS

HEADER_FILL = PatternFill(fill_type="solid", fgColor="1F4E78")
HEADER_FONT = Font(bold=True, color="FFFFFF")


def _write_sheet(workbook: Workbook, sheet_name: str) -> None:
    sheet = workbook.create_sheet(sheet_name)
    sheet.append(list(REQUIRED_COLUMNS[sheet_name]))
    for cell in sheet[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
    sheet.freeze_panes = "A2"
    for column_cells in sheet.columns:
        sheet.column_dimensions[column_cells[0].column_letter].width = 24


def build_workbook(force: bool = False) -> None:
    MASTER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIGURATION_WORKBOOK.exists():
        if not force:
            raise FileExistsError(
                f"Configuration workbook already exists: {CONFIGURATION_WORKBOOK}\n"
                "No changes were made. Use --force only when you intentionally want a new template."
            )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = CONFIGURATION_WORKBOOK.with_name(
            f"{CONFIGURATION_WORKBOOK.stem}.backup_{timestamp}{CONFIGURATION_WORKBOOK.suffix}"
        )
        shutil.copy2(CONFIGURATION_WORKBOOK, backup)
        print(f"Backup created: {backup}")

    workbook = Workbook()
    workbook.remove(workbook.active)
    for sheet_name in ALL_SHEETS:
        _write_sheet(workbook, sheet_name)
    workbook.save(CONFIGURATION_WORKBOOK)
    print(f"Configuration template created: {CONFIGURATION_WORKBOOK}")
    print("Populate master data and business rules before running screening.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create RecruitOS configuration workbook template.")
    parser.add_argument("--force", action="store_true", help="Back up and replace an existing workbook.")
    args = parser.parse_args()
    try:
        build_workbook(force=args.force)
    except FileExistsError as exc:
        print(exc)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
