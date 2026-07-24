"""
============================================================
RecruitOS

Module      : Path Configuration
Sprint      : 5.5.0.1
Version     : 1.0.0
Author       : Tamilvanan A

Purpose:
Centralizes all application paths.

Every module must import paths only from here.

============================================================
"""

from pathlib import Path

# ============================================================
# Project Root
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ============================================================
# Application Directories
# ============================================================

CONFIG_DIR = PROJECT_ROOT / "config"

DATABASE_DIR = PROJECT_ROOT / "database"

MODELS_DIR = PROJECT_ROOT / "models"

PARSER_DIR = PROJECT_ROOT / "parser"

SERVICES_DIR = PROJECT_ROOT / "services"

UTILS_DIR = PROJECT_ROOT / "utils"

UI_DIR = PROJECT_ROOT / "ui"

TESTS_DIR = PROJECT_ROOT / "tests"

TOOLS_DIR = PROJECT_ROOT / "tools"

DOCS_DIR = PROJECT_ROOT / "docs"

MASTER_DATA_DIR = PROJECT_ROOT / "Master_Data"

UPLOADS_DIR = PROJECT_ROOT / "uploads"

OUTPUT_DIR = PROJECT_ROOT / "output"

LOGS_DIR = PROJECT_ROOT / "logs"

TEMP_DIR = PROJECT_ROOT / "temp"

# ============================================================
# Master Configuration Workbook
# ============================================================

CONFIGURATION_WORKBOOK = (
    MASTER_DATA_DIR /
    "RecruitOS_Configuration.xlsx"
)

# ============================================================
# Helper
# ============================================================

ALL_DIRECTORIES = [

    DATABASE_DIR,

    MASTER_DATA_DIR,

    OUTPUT_DIR,

    LOGS_DIR,

    TEMP_DIR,

    DOCS_DIR,

    UPLOADS_DIR

]

# ============================================================
# Create Directories
# ============================================================

for directory in ALL_DIRECTORIES:

    directory.mkdir(

        parents=True,

        exist_ok=True

    )