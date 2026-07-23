"""
============================================================
RecruitOS - AI Recruitment Platform
Module : Settings
Version: 0.4.0
Author : Tamilvanan A
============================================================
"""

from pathlib import Path

# ============================================================
# Application Information
# ============================================================

APP_NAME = "RecruitOS"

VERSION = "0.4.0"

AUTHOR = "Tamilvanan A"

COMPANY = "RecruitOS Enterprise"

# ============================================================
# Project Root
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ============================================================
# Folder Structure
# ============================================================

RESUME_FOLDER = PROJECT_ROOT / "Resume"

JD_FOLDER = PROJECT_ROOT / "JD"

SKILL_LIST_FOLDER = PROJECT_ROOT / "Skill_List"

OUTPUT_FOLDER = PROJECT_ROOT / "output"

TEMP_FOLDER = PROJECT_ROOT / "temp"

LOG_FOLDER = PROJECT_ROOT / "logs"

DATABASE_FOLDER = PROJECT_ROOT / "database"

# ============================================================
# Required Folder List
# ============================================================

REQUIRED_FOLDERS = [
    RESUME_FOLDER,
    JD_FOLDER,
    SKILL_LIST_FOLDER,
    OUTPUT_FOLDER,
    TEMP_FOLDER,
    LOG_FOLDER,
    DATABASE_FOLDER
]

# ============================================================
# Automatically Create Folders
# ============================================================

for folder in REQUIRED_FOLDERS:
    folder.mkdir(parents=True, exist_ok=True)

# ============================================================
# Supported File Types
# ============================================================

SUPPORTED_RESUME_TYPES = [
    ".pdf",
    ".docx",
    ".txt"
]

SUPPORTED_JD_TYPES = [
    ".pdf",
    ".docx",
    ".txt"
]

SUPPORTED_SKILL_TYPES = [
    ".xlsx",
    ".csv",
    ".txt"
]

# ============================================================
# Upload Limits
# ============================================================

MAX_FILE_SIZE_MB = 20

MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# ============================================================
# Report Configuration
# ============================================================

DEFAULT_REPORT_NAME = "Candidate_Report.xlsx"

# ============================================================
# Logging
# ============================================================

LOG_FILE = LOG_FOLDER / "recruitos.log"

# ============================================================
# Database
# ============================================================

DATABASE_NAME = "recruitos.db"

DATABASE_PATH = DATABASE_FOLDER / DATABASE_NAME