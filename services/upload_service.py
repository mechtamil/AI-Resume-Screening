"""
============================================================
RecruitOS - AI Recruitment Platform
Module : Upload Service
Version: 0.4.0
Author : Tamilvanan A
============================================================
"""

from pathlib import Path
import shutil

from config.settings import (
    JD_FOLDER,
    RESUME_FOLDER,
    SKILL_LIST_FOLDER,
)


class UploadService:
    """
    Handles all uploaded file storage.
    """

    @staticmethod
    def save_job_description(uploaded_file):

        if uploaded_file is None:
            return None

        destination = JD_FOLDER / uploaded_file.name

        with open(destination, "wb") as file:
            file.write(uploaded_file.getbuffer())

        return destination

    @staticmethod
    def save_skill_list(uploaded_file):

        if uploaded_file is None:
            return None

        destination = SKILL_LIST_FOLDER / uploaded_file.name

        with open(destination, "wb") as file:
            file.write(uploaded_file.getbuffer())

        return destination

    @staticmethod
    def save_resume(uploaded_file):

        if uploaded_file is None:
            return None

        destination = RESUME_FOLDER / uploaded_file.name

        with open(destination, "wb") as file:
            file.write(uploaded_file.getbuffer())

        return destination

    @staticmethod
    def save_multiple_resumes(uploaded_files):

        saved_files = []

        if not uploaded_files:
            return saved_files

        for uploaded_file in uploaded_files:

            destination = RESUME_FOLDER / uploaded_file.name

            with open(destination, "wb") as file:
                file.write(uploaded_file.getbuffer())

            saved_files.append(destination)

        return saved_files

    @staticmethod
    def clear_folder(folder_path: Path):

        if not folder_path.exists():
            return

        for item in folder_path.iterdir():

            if item.is_file():
                item.unlink()

            elif item.is_dir():
                shutil.rmtree(item)