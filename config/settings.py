"""Application-level settings for RecruitOS.

Filesystem paths live in :mod:`config.paths`. This module exposes application
metadata, supported file types, upload limits, and compatibility aliases used
by older modules.
"""
from __future__ import annotations

from config.paths import (
    DATABASE_PATH,
    LOG_FILE,
    OUTPUT_DIR,
    TEMP_DIR,
    UPLOAD_JD_DIR,
    UPLOAD_RESUME_DIR,
    UPLOAD_SKILL_LIST_DIR,
    VERSION_FILE,
)

APP_NAME = "RecruitOS"
AUTHOR = "Tamilvanan A"
COMPANY = "RecruitOS Enterprise"


def _read_version() -> str:
    try:
        value = VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return "0.0.0-dev"
    return value or "0.0.0-dev"


VERSION = _read_version()

SUPPORTED_RESUME_TYPES = (".pdf", ".docx", ".txt")
SUPPORTED_JD_TYPES = (".pdf", ".docx", ".txt")
SUPPORTED_SKILL_TYPES = (".xlsx", ".csv", ".txt")
SUPPORTED_EXTENSIONS = tuple(
    sorted(set(SUPPORTED_RESUME_TYPES + SUPPORTED_JD_TYPES + SUPPORTED_SKILL_TYPES))
)

MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
DEFAULT_REPORT_NAME = "Candidate_Report.xlsx"

# Compatibility aliases. New code should prefer config.paths directly.
JD_FOLDER = UPLOAD_JD_DIR
RESUME_FOLDER = UPLOAD_RESUME_DIR
SKILL_LIST_FOLDER = UPLOAD_SKILL_LIST_DIR
OUTPUT_FOLDER = OUTPUT_DIR
TEMP_FOLDER = TEMP_DIR
DATABASE_FOLDER = DATABASE_PATH.parent
DATABASE_NAME = DATABASE_PATH.name
