"""
============================================================
RecruitOS
Configuration - Project Paths

Version : 1.0
Author  : Tamilvanan A

Description:
Centralized path management for the RecruitOS project.

All project modules should import paths from this file
instead of hardcoding file or folder locations.
============================================================
"""

from pathlib import Path

# ============================================================
# Project Root
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ============================================================
# Data Directories
# ============================================================

MASTER_DATA_DIR = PROJECT_ROOT / "Master_Data"

JD_DIR = PROJECT_ROOT / "JD"

RESUME_DIR = PROJECT_ROOT / "Resume"

OUTPUT_DIR = PROJECT_ROOT / "output"

REPORT_DIR = PROJECT_ROOT / "reports"

LOG_DIR = PROJECT_ROOT / "logs"

TEMP_DIR = PROJECT_ROOT / "temp"

# ============================================================
# Master Data Files
# ============================================================

SKILLS_MASTER_FILE = MASTER_DATA_DIR / "skills_master.xlsx"

# ============================================================
# Application Directories
# ============================================================

CONFIG_DIR = PROJECT_ROOT / "config"

MODELS_DIR = PROJECT_ROOT / "models"

PARSER_DIR = PROJECT_ROOT / "parser"

SERVICES_DIR = PROJECT_ROOT / "services"

UI_DIR = PROJECT_ROOT / "ui"

TOOLS_DIR = PROJECT_ROOT / "tools"

TESTS_DIR = PROJECT_ROOT / "tests"

# ============================================================
# List of Directories to Auto-Create
# ============================================================

ALL_DIRECTORIES = [

    MASTER_DATA_DIR,

    JD_DIR,

    RESUME_DIR,

    OUTPUT_DIR,

    REPORT_DIR,

    LOG_DIR,

    TEMP_DIR

]

# ============================================================
# Create Missing Directories
# ============================================================

def ensure_directories():
    """
    Create all required RecruitOS directories if they do not exist.
    """

    for directory in ALL_DIRECTORIES:

        directory.mkdir(
            parents=True,
            exist_ok=True
        )

# ============================================================
# Execute on Import
# ============================================================

ensure_directories()

# ============================================================
# Debug
# ============================================================

if __name__ == "__main__":

    print("\n========== RecruitOS Paths ==========\n")

    print("Project Root :", PROJECT_ROOT)

    print("Master Data  :", MASTER_DATA_DIR)

    print("Skills File  :", SKILLS_MASTER_FILE)

    print("JD Folder    :", JD_DIR)

    print("Resume Folder:", RESUME_DIR)

    print("Output Folder:", OUTPUT_DIR)

    print("Reports      :", REPORT_DIR)

    print("Logs         :", LOG_DIR)

    print("Temp         :", TEMP_DIR)

    print("\nDirectories verified successfully.\n")

# =====================================================
# Master Data Files
# =====================================================

SKILLS_MASTER_FILE = MASTER_DATA_DIR / "skills_master.xlsx"

CERTIFICATION_MASTER_FILE = (
    MASTER_DATA_DIR / "certification_master.xlsx"
)

EDUCATION_MASTER_FILE = (
    MASTER_DATA_DIR / "education_master.xlsx"
)

COMPANY_MASTER_FILE = (
    MASTER_DATA_DIR / "company_master.xlsx"
)

LOCATION_MASTER_FILE = (
    MASTER_DATA_DIR / "location_master.xlsx"
)

LANGUAGE_MASTER_FILE = (
    MASTER_DATA_DIR / "language_master.xlsx"
)

DOMAIN_MASTER_FILE = (
    MASTER_DATA_DIR / "domain_master.xlsx"
)