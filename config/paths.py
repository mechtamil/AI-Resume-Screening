"""Central filesystem paths for RecruitOS.

All runtime modules must import filesystem locations from this module instead of
constructing project-relative paths independently.
"""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_DIR = PROJECT_ROOT / "config"
DATABASE_DIR = PROJECT_ROOT / "database"
DOCS_DIR = PROJECT_ROOT / "docs"
MASTER_DATA_DIR = PROJECT_ROOT / "Master_Data"
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUT_DIR = PROJECT_ROOT / "output"
PARSER_DIR = PROJECT_ROOT / "parser"
REPORTS_DIR = PROJECT_ROOT / "reports"
SERVICES_DIR = PROJECT_ROOT / "services"
TEMP_DIR = PROJECT_ROOT / "temp"
TESTS_DIR = PROJECT_ROOT / "tests"
TOOLS_DIR = PROJECT_ROOT / "tools"
UI_DIR = PROJECT_ROOT / "ui"
UPLOADS_DIR = PROJECT_ROOT / "uploads"
UTILS_DIR = PROJECT_ROOT / "utils"

# Runtime upload storage. These folders are intentionally separated from
# source-controlled JD/Resume fixtures.
UPLOAD_JD_DIR = UPLOADS_DIR / "job_descriptions"
UPLOAD_RESUME_DIR = UPLOADS_DIR / "resumes"
UPLOAD_SKILL_LIST_DIR = UPLOADS_DIR / "skill_lists"

CONFIGURATION_WORKBOOK = MASTER_DATA_DIR / "RecruitOS_Configuration.xlsx"
DATABASE_PATH = DATABASE_DIR / "recruitos.db"
LOG_FILE = PROJECT_ROOT / "logs" / "recruitos.log"
VERSION_FILE = PROJECT_ROOT / "VERSION"

RUNTIME_DIRECTORIES = (
    DATABASE_DIR,
    DOCS_DIR,
    MASTER_DATA_DIR,
    OUTPUT_DIR,
    REPORTS_DIR,
    TEMP_DIR,
    UPLOADS_DIR,
    UPLOAD_JD_DIR,
    UPLOAD_RESUME_DIR,
    UPLOAD_SKILL_LIST_DIR,
    LOG_FILE.parent,
)


def ensure_runtime_directories() -> None:
    """Create application-owned runtime directories if they do not exist."""
    for directory in RUNTIME_DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)


ensure_runtime_directories()
