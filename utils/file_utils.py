"""
============================================================
RecruitOS - AI Recruitment Platform
Module : File Utilities
Version: 0.3.0
Author : Tamilvanan A
============================================================
"""

from pathlib import Path

from config.settings import (
    SUPPORTED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES
)


def get_extension(file_name):

    return Path(file_name).suffix.lower()


def is_supported(file_name):

    extension = get_extension(file_name)

    return extension in SUPPORTED_EXTENSIONS


def get_size(uploaded_file):

    return uploaded_file.size


def size_in_mb(uploaded_file):

    return round(uploaded_file.size / (1024 * 1024), 2)


def validate(uploaded_file):

    errors = []

    extension = get_extension(uploaded_file.name)

    if extension not in SUPPORTED_EXTENSIONS:

        errors.append(
            f"Unsupported file type : {extension}"
        )

    if uploaded_file.size > MAX_FILE_SIZE_BYTES:

        errors.append(
            "File exceeds maximum allowed size."
        )

    return errors