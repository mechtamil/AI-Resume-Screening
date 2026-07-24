"""Safe runtime storage for uploaded recruitment files."""
from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from config.paths import UPLOAD_JD_DIR, UPLOAD_RESUME_DIR, UPLOAD_SKILL_LIST_DIR
from config.settings import SUPPORTED_JD_TYPES, SUPPORTED_RESUME_TYPES, SUPPORTED_SKILL_TYPES
from utils.file_utils import validate


class UploadService:
    @staticmethod
    def _safe_name(name: str) -> str:
        base = Path(name or "upload").name
        stem = re.sub(r"[^A-Za-z0-9._ -]+", "_", Path(base).stem).strip(" ._") or "upload"
        suffix = re.sub(r"[^A-Za-z0-9.]", "", Path(base).suffix.lower())
        return f"{stem[:120]}_{uuid4().hex[:10]}{suffix}"

    @classmethod
    def _save(cls, uploaded_file, destination_dir: Path, allowed_extensions: tuple[str, ...]) -> Path | None:
        if uploaded_file is None:
            return None
        errors = validate(uploaded_file, allowed_extensions)
        if errors:
            raise ValueError("; ".join(errors))
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / cls._safe_name(uploaded_file.name)
        destination.write_bytes(bytes(uploaded_file.getbuffer()))
        return destination

    @classmethod
    def save_job_description(cls, uploaded_file) -> Path | None:
        return cls._save(uploaded_file, UPLOAD_JD_DIR, SUPPORTED_JD_TYPES)

    @classmethod
    def save_skill_list(cls, uploaded_file) -> Path | None:
        return cls._save(uploaded_file, UPLOAD_SKILL_LIST_DIR, SUPPORTED_SKILL_TYPES)

    @classmethod
    def save_resume(cls, uploaded_file) -> Path | None:
        return cls._save(uploaded_file, UPLOAD_RESUME_DIR, SUPPORTED_RESUME_TYPES)

    @classmethod
    def save_multiple_resumes(cls, uploaded_files) -> list[Path]:
        return [path for path in (cls.save_resume(item) for item in (uploaded_files or [])) if path]

    @staticmethod
    def clear_folder(folder_path: Path) -> None:
        """Remove runtime files only; caller controls which runtime directory is supplied."""
        if not folder_path.exists():
            return
        for item in folder_path.iterdir():
            if item.is_file():
                item.unlink()
