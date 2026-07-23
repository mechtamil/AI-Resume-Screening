"""
============================================================
RecruitOS - AI Recruitment Platform
Module : Settings
Version: 0.3.0
Author : Tamilvanan A
============================================================
"""

from pathlib import Path

# ============================================================
# Application
# ============================================================

APP_NAME = "RecruitOS"

VERSION = "0.3.0"

AUTHOR = "Tamilvanan A"

# ============================================================
# Project Root
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ============================================================
# Folder Structure
# ============================================================

RESUME_FOLDER = PROJECT_ROOT / "Resume"

JD_FOLDER = PROJECT_ROOT / "JD"

OUTPUT_FOLDER = PROJECT_ROOT / "output"

TEMP_FOLDER = PROJECT_ROOT / "temp"

LOG_FOLDER = PROJECT_ROOT / "logs"

DATABASE_FOLDER = PROJECT_ROOT / "database"

# ============================================================
# File Configuration
# ============================================================

SUPPORTED_EXTENSIONS = [
    ".pdf",
    ".docx",
    ".txt"
]

MAX_FILE_SIZE_MB = 20

MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# ============================================================
# Create folders automatically
# ============================================================

REQUIRED_FOLDERS = [
    RESUME_FOLDER,
    JD_FOLDER,
    OUTPUT_FOLDER,
    TEMP_FOLDER,
    LOG_FOLDER,
    DATABASE_FOLDER
]

for folder in REQUIRED_FOLDERS:
    folder.mkdir(parents=True, exist_ok=True)