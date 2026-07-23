"""
============================================================
RecruitOS - AI Recruitment Platform
Module      : Candidate Repository
Version     : 0.4.1
Author      : Tamilvanan A

Description:
Handles all Candidate database operations.
============================================================
"""

from database.database import Database


class CandidateRepository:

    def __init__(self):

        self.db = Database()

    def add_candidate(
        self,
        full_name,
        email,
        phone,
        experience,
        current_company,
        location,
        notice_period,
        current_ctc,
        expected_ctc,
        status="New"
    ):

        self.db.cursor.execute(
            """
            INSERT INTO candidates
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
                status
            )

            VALUES
            (?,?,?,?,?,?,?,?,?,?)
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
                status
            )
        )

        self.db.connection.commit()

    def get_all_candidates(self):

        self.db.cursor.execute(
            """
            SELECT *
            FROM candidates
            ORDER BY id DESC
            """
        )

        return self.db.cursor.fetchall()

    def get_candidate_count(self):

        self.db.cursor.execute(
            """
            SELECT COUNT(*)
            FROM candidates
            """
        )

        return self.db.cursor.fetchone()[0]

    def close(self):

        self.db.close()