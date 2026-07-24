"""SQLite database connection and schema bootstrap for RecruitOS."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from config.paths import DATABASE_PATH


class Database:
    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = Path(database_path or DATABASE_PATH)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.connection.cursor()

    def create_tables(self) -> None:
        self.cursor.execute(
            """
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
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
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
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                file_name TEXT,
                file_type TEXT,
                file_size INTEGER,
                page_count INTEGER,
                word_count INTEGER,
                character_count INTEGER,
                file_hash TEXT,
                uploaded_time TEXT,
                FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
            )
            """
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()
