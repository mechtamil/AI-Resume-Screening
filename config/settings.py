"""Application-level settings for RecruitOS.

Filesystem paths live in :mod:`config.paths`. Security values are deployment
configuration—not user-facing business data. Environment variables take priority;
Streamlit secrets provide a deployment-friendly fallback.
"""
from __future__ import annotations

import os
from typing import Any

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
COMPANY = "ALTEN"


def _deployment_value(name: str, default: Any = None) -> Any:
    """Read a deployment value from environment, then Streamlit secrets.

    Importing Streamlit is optional so command-line tools and unit tests remain
    independent of a running Streamlit context.
    """
    environment_value = os.getenv(name)
    if environment_value is not None:
        return environment_value

    try:
        import streamlit as st

        secrets = st.secrets
        if name in secrets:
            return secrets[name]
    except Exception:
        pass
    return default


def _read_version() -> str:
    try:
        value = VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return "0.0.0-dev"
    return value or "0.0.0-dev"


def _environment_flag(name: str, default: bool) -> bool:
    raw_value = _deployment_value(name)
    if raw_value is None:
        return default
    return str(raw_value).strip().casefold() in {"1", "true", "yes", "on"}


def _environment_int(name: str, default: int, *, minimum: int = 0) -> int:
    try:
        value = int(str(_deployment_value(name, default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, value)


DEPLOYMENT_ENVIRONMENT = str(
    _deployment_value("RECRUITOS_ENVIRONMENT", "production")
).strip().casefold()
if DEPLOYMENT_ENVIRONMENT not in {"development", "test", "production"}:
    DEPLOYMENT_ENVIRONMENT = "production"

VERSION = _read_version()

DOCUMENT_TEXT_TYPES = (".pdf", ".docx", ".txt")
DOCUMENT_SPREADSHEET_TYPES = (".xlsx", ".xls", ".csv")
DOCUMENT_IMAGE_TYPES = (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff")

# RecruitOS accepts common recruitment-document formats across all three input
# groups. Image and scanned-PDF text is extracted through the OCR adapter.
SUPPORTED_RESUME_TYPES = tuple(
    dict.fromkeys(DOCUMENT_TEXT_TYPES + DOCUMENT_SPREADSHEET_TYPES + DOCUMENT_IMAGE_TYPES)
)
SUPPORTED_JD_TYPES = tuple(
    dict.fromkeys(DOCUMENT_TEXT_TYPES + DOCUMENT_SPREADSHEET_TYPES + DOCUMENT_IMAGE_TYPES)
)
SUPPORTED_SKILL_TYPES = tuple(
    dict.fromkeys(DOCUMENT_SPREADSHEET_TYPES + DOCUMENT_TEXT_TYPES + DOCUMENT_IMAGE_TYPES)
)
SUPPORTED_EXTENSIONS = tuple(
    sorted(set(SUPPORTED_RESUME_TYPES + SUPPORTED_JD_TYPES + SUPPORTED_SKILL_TYPES))
)

MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_RESUMES_PER_SCREENING = _environment_int(
    "RECRUITOS_MAX_RESUMES_PER_SCREENING",
    100,
    minimum=1,
)
DEFAULT_REPORT_NAME = "Candidate_Report.xlsx"

# OCR runtime path is deployment configuration. It is intentionally optional:
# - local Windows/macOS/Linux can set RECRUITOS_TESSERACT_CMD,
# - any deployment with "tesseract" on PATH can leave it empty,
# - Streamlit Cloud installs tesseract-ocr through packages.txt.
TESSERACT_CMD = str(
    _deployment_value("RECRUITOS_TESSERACT_CMD", "")
).strip()
OCR_LANGUAGES = str(
    _deployment_value("RECRUITOS_OCR_LANGUAGES", "eng")
).strip() or "eng"
OCR_PAGE_SEGMENTATION_MODE = _environment_int(
    "RECRUITOS_OCR_PSM",
    3,
    minimum=0,
)
OCR_PAGE_SEGMENTATION_MODE = min(13, OCR_PAGE_SEGMENTATION_MODE)

# AI provider deployment configuration. Secrets are resolved only from the
# process environment or Streamlit secrets and are never persisted in SQLite,
# audit events, telemetry, exports, or source-controlled configuration.
AI_OPENAI_API_KEY = str(
    _deployment_value("RECRUITOS_OPENAI_API_KEY", "")
).strip()
AI_OPENAI_BASE_URL = str(
    _deployment_value("RECRUITOS_OPENAI_BASE_URL", "https://api.openai.com/v1")
).strip().rstrip("/")
AI_OLLAMA_BASE_URL = str(
    _deployment_value("RECRUITOS_OLLAMA_BASE_URL", "http://127.0.0.1:11434")
).strip().rstrip("/")
AI_HTTP_TIMEOUT_SECONDS = _environment_int(
    "RECRUITOS_AI_HTTP_TIMEOUT_SECONDS",
    60,
    minimum=5,
)
AI_MAX_RESPONSE_BYTES = _environment_int(
    "RECRUITOS_AI_MAX_RESPONSE_BYTES",
    2_000_000,
    minimum=32_768,
)
AI_DEFAULT_MAX_INPUT_CHARS = _environment_int(
    "RECRUITOS_AI_DEFAULT_MAX_INPUT_CHARS",
    120_000,
    minimum=1_000,
)
AI_DEFAULT_DAILY_REQUEST_LIMIT = _environment_int(
    "RECRUITOS_AI_DEFAULT_DAILY_REQUEST_LIMIT",
    100,
    minimum=1,
)

# Public self-registration is intentionally disabled. Users are provisioned by
# the System Owner, Global Admin, or a scope-limited Tenant Admin.
ALLOW_SELF_REGISTRATION = False

AUTH_SESSION_HOURS = _environment_int(
    "RECRUITOS_AUTH_SESSION_HOURS",
    8,
    minimum=1,
)
AUTH_MAX_FAILED_LOGINS = _environment_int(
    "RECRUITOS_AUTH_MAX_FAILED_LOGINS",
    5,
    minimum=3,
)
AUTH_LOCKOUT_MINUTES = _environment_int(
    "RECRUITOS_AUTH_LOCKOUT_MINUTES",
    15,
    minimum=1,
)

# Temporary credentials are created through the Admin UI or Excel import. No
# shared/default password is stored in source code.
AUTH_TEMP_PASSWORD_EXPIRY_DAYS = _environment_int(
    "RECRUITOS_TEMP_PASSWORD_EXPIRY_DAYS",
    7,
    minimum=0,
)
AUTH_TEMP_PASSWORD_MIN_LENGTH = _environment_int(
    "RECRUITOS_TEMP_PASSWORD_MIN_LENGTH",
    6,
    minimum=6,
)
AUTH_PERMANENT_PASSWORD_MIN_LENGTH = _environment_int(
    "RECRUITOS_PERMANENT_PASSWORD_MIN_LENGTH",
    8,
    minimum=8,
)

# One-time System Owner bootstrap protection. Shared/public deployments fail
# closed when no setup key is configured. An insecure bootstrap is allowed only
# when both the deployment environment and explicit local-development flag permit it.
INITIAL_SETUP_KEY = str(
    _deployment_value("RECRUITOS_INITIAL_SETUP_KEY", "")
).strip()
ALLOW_INSECURE_LOCAL_BOOTSTRAP = _environment_flag(
    "RECRUITOS_ALLOW_INSECURE_LOCAL_BOOTSTRAP",
    False,
)
INITIAL_OWNER_SETUP_ENABLED = bool(INITIAL_SETUP_KEY) or (
    DEPLOYMENT_ENVIRONMENT in {"development", "test"}
    and ALLOW_INSECURE_LOCAL_BOOTSTRAP
)

# Forgot-password requests are recorded for administrator action in this sprint.
# Email delivery is intentionally not simulated.
FORGOT_PASSWORD_GENERIC_MESSAGE = (
    "If the User ID is registered, a password-reset request has been recorded. "
    "Contact your RecruitOS administrator for the temporary credential."
)

# Compatibility aliases. New code should prefer config.paths directly.
JD_FOLDER = UPLOAD_JD_DIR
RESUME_FOLDER = UPLOAD_RESUME_DIR
SKILL_LIST_FOLDER = UPLOAD_SKILL_LIST_DIR
OUTPUT_FOLDER = OUTPUT_DIR
TEMP_FOLDER = TEMP_DIR
DATABASE_FOLDER = DATABASE_PATH.parent
DATABASE_NAME = DATABASE_PATH.name
