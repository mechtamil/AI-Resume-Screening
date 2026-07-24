"""Candidate persistence repository."""
from __future__ import annotations

from pathlib import Path

from database.database import Database


class CandidateRepository:
    def __init__(self, database_path: str | Path | None = None) -> None:
        self.db = Database(database_path)
        self.db.create_tables()

    def add_candidate(
        self,
        full_name,
        email="",
        phone="",
        experience=0.0,
        current_company="",
        location="",
        notice_period="",
        current_ctc="",
        expected_ctc="",
        status="New",
    ) -> int:
        self.db.cursor.execute(
            """
            INSERT INTO candidates
            (full_name, email, phone, experience, current_company, location,
             notice_period, current_ctc, expected_ctc, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                full_name,
                email,
                phone,
                experience,
                current_company,
                location,
                notice_period,
                current_ctc,
                expected_ctc,
                status,
            ),
        )
        self.db.connection.commit()
        return int(self.db.cursor.lastrowid)

    def get_all_candidates(self):
        self.db.cursor.execute("SELECT * FROM candidates ORDER BY id DESC")
        return self.db.cursor.fetchall()

    def get_candidate_count(self) -> int:
        self.db.cursor.execute("SELECT COUNT(*) FROM candidates")
        return int(self.db.cursor.fetchone()[0])

    def close(self) -> None:
        self.db.close()
