"""Spreadsheet and CSV text extraction for structured recruitment inputs."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


SECTION_FIELDS = {
    "mandatory skills",
    "preferred skills",
    "education",
    "certifications",
    "responsibilities",
    "keywords",
    "notes",
    "skills",
    "technical skills",
    "projects",
    "work experience",
    "experience",
}


def _clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.casefold() in {"nan", "none", "nat"}:
        return ""
    return text


def _split_multivalue(value: str) -> list[str]:
    values = re.split(r"[\n;|]+", value or "")
    output: list[str] = []
    for item in values:
        cleaned = item.strip(" \t,-•")
        if cleaned:
            output.append(cleaned)
    return output


def _field_value_sheet(frame: pd.DataFrame) -> str | None:
    columns = {str(column).strip().casefold(): column for column in frame.columns}
    field_column = columns.get("field") or columns.get("section") or columns.get("attribute")
    value_column = columns.get("value") or columns.get("content") or columns.get("details")
    if field_column is None or value_column is None:
        return None

    lines: list[str] = []
    for _, row in frame.iterrows():
        field = _clean(row.get(field_column))
        value = _clean(row.get(value_column))
        if not field or not value:
            continue
        if field.casefold() in SECTION_FIELDS:
            lines.append(field)
            values = _split_multivalue(value)
            lines.extend(values or [value])
        else:
            lines.append(f"{field}: {value}")
    return "\n".join(lines).strip()


def _generic_sheet(frame: pd.DataFrame) -> str:
    lines: list[str] = []
    for _, row in frame.iterrows():
        row_lines: list[str] = []
        for column in frame.columns:
            value = _clean(row.get(column))
            if value:
                row_lines.append(f"{str(column).strip()}: {value}")
        if row_lines:
            lines.extend(row_lines)
            lines.append("")
    return "\n".join(lines).strip()


def _frame_to_text(frame: pd.DataFrame) -> str:
    if frame.empty:
        return ""
    structured = _field_value_sheet(frame)
    return structured if structured is not None else _generic_sheet(frame)


def read_spreadsheet(file_path: str | Path) -> str:
    """Read XLSX/XLS/CSV data and convert all populated sheets to text."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Spreadsheet not found: {path}")

    extension = path.suffix.casefold()
    try:
        if extension == ".csv":
            frames = {path.stem: pd.read_csv(path, dtype=str, keep_default_na=False)}
        elif extension in {".xlsx", ".xls"}:
            frames = pd.read_excel(
                path,
                sheet_name=None,
                dtype=str,
                keep_default_na=False,
            )
        else:
            raise ValueError(f"Unsupported spreadsheet type: {extension}")
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Unable to read spreadsheet: {path}") from exc

    sections: list[str] = []
    for sheet_name, frame in frames.items():
        text = _frame_to_text(frame)
        if text:
            sections.append(text)
    return "\n\n".join(sections).strip()
