"""File validation helpers used by upload workflows."""
from __future__ import annotations

from pathlib import Path

from config.settings import MAX_FILE_SIZE_BYTES, SUPPORTED_EXTENSIONS


def get_extension(file_name: str) -> str:
    return Path(file_name).suffix.lower()


def is_supported(file_name: str, allowed_extensions: tuple[str, ...] | None = None) -> bool:
    allowed = allowed_extensions or SUPPORTED_EXTENSIONS
    return get_extension(file_name) in allowed


def get_size(uploaded_file) -> int:
    return int(getattr(uploaded_file, "size", 0))


def size_in_mb(uploaded_file) -> float:
    return round(get_size(uploaded_file) / (1024 * 1024), 2)


def validate(uploaded_file, allowed_extensions: tuple[str, ...] | None = None) -> list[str]:
    errors: list[str] = []
    if uploaded_file is None:
        return ["No file was provided."]
    allowed = allowed_extensions or SUPPORTED_EXTENSIONS
    extension = get_extension(getattr(uploaded_file, "name", ""))
    if extension not in allowed:
        errors.append(f"Unsupported file type: {extension or '<none>'}")
    if get_size(uploaded_file) > MAX_FILE_SIZE_BYTES:
        errors.append("File exceeds the maximum allowed size.")
    return errors
