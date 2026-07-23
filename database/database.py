
"""
============================================================
RecruitOS - AI Recruitment Platform
Module      : Database
Version     : 0.4.0
Author      : Tamilvanan A

Description:
Creates and manages the RecruitOS SQLite database.
============================================================
"""

import sqlite3
from pathlib import Path

# Database file
DATABASE_PATH = Path(__file__).parent / "recruitos.db"


class Database:

    def __init__(self):
        self.connection = sqlite3.connect(DATABASE_PATH)
        self.cursor = self.connection.cursor()

    def create_tables(self):
        """
        Create all RecruitOS tables.
        """

        # Recruitment Projects
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS recruitment_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT,
            client_name TEXT,
            job_title TEXT,
            hiring_manager TEXT,
            location TEXT,
            target_headcount INTEGER,
            status TEXT
        )
        """)

        # Candidates
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            experience REAL,
            current_company TEXT,
            location TEXT,
            notice_period TEXT,
            current_ctc TEXT,
            expected_ctc TEXT,
            status TEXT
        )
        """)

        # Resumes
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER,
            file_name TEXT,
            file_type TEXT,
            file_size INTEGER,
            page_count INTEGER,
            word_count INTEGER,
            character_count INTEGER,
            file_hash TEXT,
            uploaded_time TEXT
        )
        """)

        self.connection.commit()

    def close(self):
        self.connection.close()