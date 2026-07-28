"""Private candidate persistence repository with domain-model mapping."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from database.database import Database
from models.candidate import Candidate
from models.security_context import SecurityContext


class CandidateRepository:
    """Persist and retrieve candidates only inside the current private workspace."""

    def __init__(
        self,
        context: SecurityContext,
        database: Database | str | Path | None = None,
    ) -> None:
        context.require_valid()
        self.context = context
        self._owns_database = not isinstance(database, Database)
        self.db = database if isinstance(database, Database) else Database(database)
        self.db.create_tables()

    def add_candidate_model(
        self,
        candidate: Candidate,
        *,
        project_id: int | None = None,
        session_id: int | None = None,
        candidate_key: str = "",
        status: str = "Processed",
        commit: bool = True,
    ) -> int:
        if project_id is not None and not self._project_is_owned(project_id):
            raise PermissionError("The selected recruitment project is not available.")
        if session_id is not None and not self._session_is_owned(session_id):
            raise PermissionError("The selected screening session is not available.")

        key = str(candidate_key or "").strip() or uuid4().hex
        companies = list(candidate.companies or [])
        current_company = companies[0] if companies else ""
        created_at = self._utc_now()

        cursor = self.db.connection.execute(
            """
            INSERT INTO candidates
            (tenant_id, created_by_user_id, project_id, session_id,
             candidate_key, full_name, email, phone, location, linkedin,
             github, website, designation, experience, total_experience,
             current_company, education_json, certifications_json,
             technical_skills_json, soft_skills_json, tools_json,
             projects_json, companies_json, source_file, raw_text,
             status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.context.tenant_id,
                self.context.user_id,
                project_id,
                session_id,
                key,
                candidate.full_name,
                candidate.email,
                candidate.phone,
                candidate.location,
                candidate.linkedin,
                candidate.github,
                candidate.website,
                candidate.designation,
                float(candidate.total_experience or 0.0),
                float(candidate.total_experience or 0.0),
                current_company,
                self._dump(candidate.education),
                self._dump(candidate.certifications),
                self._dump(candidate.technical_skills),
                self._dump(candidate.soft_skills),
                self._dump(candidate.tools),
                self._dump(candidate.projects),
                self._dump(candidate.companies),
                candidate.source_file,
                candidate.raw_text,
                status,
                created_at,
            ),
        )
        if commit:
            self.db.connection.commit()
        return int(cursor.lastrowid)

    def get_candidate(self, candidate_id: int) -> Candidate | None:
        row = self.db.connection.execute(
            """
            SELECT * FROM candidates
            WHERE id = ? AND tenant_id = ? AND created_by_user_id = ?
            """,
            (int(candidate_id), self.context.tenant_id, self.context.user_id),
        ).fetchone()
        return self.row_to_candidate(row) if row else None

    def get_candidate_record(self, candidate_id: int) -> dict[str, Any] | None:
        row = self.db.connection.execute(
            """
            SELECT * FROM candidates
            WHERE id = ? AND tenant_id = ? AND created_by_user_id = ?
            """,
            (int(candidate_id), self.context.tenant_id, self.context.user_id),
        ).fetchone()
        return dict(row) if row else None

    def list_candidate_records(
        self,
        *,
        project_id: int | None = None,
        session_id: int | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        clauses = ["tenant_id = ?", "created_by_user_id = ?"]
        parameters: list[Any] = [self.context.tenant_id, self.context.user_id]

        if project_id is not None:
            clauses.append("project_id = ?")
            parameters.append(int(project_id))
        if session_id is not None:
            clauses.append("session_id = ?")
            parameters.append(int(session_id))

        parameters.append(max(1, int(limit)))
        rows = self.db.connection.execute(
            f"""
            SELECT * FROM candidates
            WHERE {' AND '.join(clauses)}
            ORDER BY id DESC
            LIMIT ?
            """,
            tuple(parameters),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_candidates(
        self,
        *,
        project_id: int | None = None,
        session_id: int | None = None,
        limit: int = 500,
    ) -> list[Candidate]:
        return [
            self.row_to_candidate(record)
            for record in self.list_candidate_records(
                project_id=project_id,
                session_id=session_id,
                limit=limit,
            )
        ]

    def get_candidate_count(self, *, project_id: int | None = None) -> int:
        if project_id is None:
            row = self.db.connection.execute(
                """
                SELECT COUNT(*) AS total FROM candidates
                WHERE tenant_id = ? AND created_by_user_id = ?
                """,
                (self.context.tenant_id, self.context.user_id),
            ).fetchone()
        else:
            row = self.db.connection.execute(
                """
                SELECT COUNT(*) AS total FROM candidates
                WHERE tenant_id = ? AND created_by_user_id = ? AND project_id = ?
                """,
                (
                    self.context.tenant_id,
                    self.context.user_id,
                    int(project_id),
                ),
            ).fetchone()
        return int(row["total"] if row else 0)

    # ------------------------------------------------------------------
    # Backward-compatible candidate APIs, now private to the current user.
    # ------------------------------------------------------------------

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
        candidate = Candidate(
            full_name=str(full_name or ""),
            email=str(email or ""),
            phone=str(phone or ""),
            location=str(location or ""),
            total_experience=float(experience or 0.0),
            companies=[str(current_company)] if current_company else [],
        )
        candidate_id = self.add_candidate_model(
            candidate,
            status=status,
            commit=False,
        )
        self.db.connection.execute(
            """
            UPDATE candidates
            SET current_company = ?, notice_period = ?, current_ctc = ?,
                expected_ctc = ?
            WHERE id = ? AND tenant_id = ? AND created_by_user_id = ?
            """,
            (
                str(current_company or ""),
                str(notice_period or ""),
                str(current_ctc or ""),
                str(expected_ctc or ""),
                candidate_id,
                self.context.tenant_id,
                self.context.user_id,
            ),
        )
        self.db.connection.commit()
        return candidate_id

    def get_all_candidates(self):
        rows = self.db.connection.execute(
            """
            SELECT id, full_name, email, phone,
                   COALESCE(total_experience, experience, 0) AS experience,
                   current_company, location, notice_period, current_ctc,
                   expected_ctc, status
            FROM candidates
            WHERE tenant_id = ? AND created_by_user_id = ?
            ORDER BY id DESC
            """,
            (self.context.tenant_id, self.context.user_id),
        ).fetchall()
        return [tuple(row) for row in rows]

    def close(self) -> None:
        if self._owns_database:
            self.db.close()

    def _project_is_owned(self, project_id: int) -> bool:
        row = self.db.connection.execute(
            """
            SELECT 1 FROM recruitment_projects
            WHERE id = ? AND tenant_id = ? AND owner_user_id = ?
            """,
            (int(project_id), self.context.tenant_id, self.context.user_id),
        ).fetchone()
        return row is not None

    def _session_is_owned(self, session_id: int) -> bool:
        row = self.db.connection.execute(
            """
            SELECT 1 FROM screening_sessions
            WHERE id = ? AND tenant_id = ? AND created_by_user_id = ?
            """,
            (int(session_id), self.context.tenant_id, self.context.user_id),
        ).fetchone()
        return row is not None

    @classmethod
    def row_to_candidate(cls, row: Any) -> Candidate:
        data = dict(row)
        return Candidate(
            full_name=str(data.get("full_name") or ""),
            email=str(data.get("email") or ""),
            phone=str(data.get("phone") or ""),
            location=str(data.get("location") or ""),
            linkedin=str(data.get("linkedin") or ""),
            github=str(data.get("github") or ""),
            website=str(data.get("website") or ""),
            designation=str(data.get("designation") or ""),
            total_experience=float(
                data.get("total_experience") or data.get("experience") or 0.0
            ),
            education=cls._load(data.get("education_json"), []),
            certifications=cls._load(data.get("certifications_json"), []),
            technical_skills=cls._load(data.get("technical_skills_json"), []),
            soft_skills=cls._load(data.get("soft_skills_json"), []),
            tools=cls._load(data.get("tools_json"), []),
            projects=cls._load(data.get("projects_json"), []),
            companies=cls._load(data.get("companies_json"), []),
            source_file=str(data.get("source_file") or ""),
            raw_text=str(data.get("raw_text") or ""),
        )

    @staticmethod
    def _dump(value: Any) -> str:
        return json.dumps(value or [], ensure_ascii=False)

    @staticmethod
    def _load(value: Any, default: Any) -> Any:
        try:
            return json.loads(str(value or ""))
        except (TypeError, ValueError, json.JSONDecodeError):
            return default

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")
