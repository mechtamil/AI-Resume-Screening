"""Private screening-session and MatchResult persistence repository."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from database.database import Database
from models.match_result import MatchResult
from models.security_context import SecurityContext


class ScreeningRepository:
    """Persist screening data only inside the authenticated user's workspace."""

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

    def create_session(
        self,
        project_id: int,
        *,
        summary: dict[str, Any] | None = None,
        errors: list[dict[str, Any]] | None = None,
        session_key: str = "",
        status: str = "Completed",
        configuration: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> int:
        if not self._project_is_owned(project_id):
            raise PermissionError("The selected recruitment project is not available.")

        summary = summary or {}
        configuration = configuration or {}
        key = str(session_key or "").strip() or uuid4().hex
        cursor = self.db.connection.execute(
            """
            INSERT INTO screening_sessions
            (tenant_id, created_by_user_id, project_id, session_key,
             resumes_requested, resumes_processed, resumes_failed,
             shortlisted_count, status, errors_json,
             configuration_version_id, configuration_sha256,
             configuration_snapshot_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.context.tenant_id,
                self.context.user_id,
                int(project_id),
                key,
                int(summary.get("resumes_requested", 0) or 0),
                int(summary.get("resumes_processed", 0) or 0),
                int(summary.get("resumes_failed", 0) or 0),
                int(summary.get("shortlisted_count", 0) or 0),
                status,
                self._dump(errors or []),
                (
                    int(configuration["version_id"])
                    if configuration.get("version_id") is not None
                    else None
                ),
                str(configuration.get("sha256") or ""),
                self._dump(configuration),
                self._utc_now(),
            ),
        )
        if commit:
            self.db.connection.commit()
        return int(cursor.lastrowid)

    def add_match_result(
        self,
        result: MatchResult,
        *,
        project_id: int,
        session_id: int,
        candidate_id: int,
        commit: bool = True,
    ) -> int:
        if not self._matching_scope_is_owned(project_id, session_id, candidate_id):
            raise PermissionError("The selected screening data is not available.")

        processed_time = result.processed_time
        if isinstance(processed_time, datetime):
            processed_time_value = processed_time.isoformat(timespec="seconds")
        else:
            processed_time_value = str(processed_time or self._utc_now())

        cursor = self.db.connection.execute(
            """
            INSERT INTO match_results
            (tenant_id, created_by_user_id, project_id, session_id, candidate_id,
             job_id, job_title, matched_skills_json, missing_skills_json,
             matched_preferred_skills_json, missing_preferred_skills_json,
             additional_skills_json, matched_certifications_json,
             missing_certifications_json, certification_match, education_match,
             required_experience, maximum_experience, candidate_experience,
             experience_match, matched_keyword_values_json,
             missing_keyword_values_json, matched_keywords, total_keywords,
             skill_score, experience_score, education_score,
             certification_score, keyword_score,
             weighted_score_breakdown_json, overall_match_percentage, rank,
             recommendation, shortlisted, status, remarks_json, processed_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.context.tenant_id,
                self.context.user_id,
                int(project_id),
                int(session_id),
                int(candidate_id),
                result.job_id,
                result.job_title,
                self._dump(result.matched_skills),
                self._dump(result.missing_skills),
                self._dump(result.matched_preferred_skills),
                self._dump(result.missing_preferred_skills),
                self._dump(result.additional_skills),
                self._dump(result.matched_certifications),
                self._dump(result.missing_certifications),
                int(bool(result.certification_match)),
                int(bool(result.education_match)),
                float(result.required_experience or 0.0),
                float(result.maximum_experience or 0.0),
                float(result.candidate_experience or 0.0),
                int(bool(result.experience_match)),
                self._dump(result.matched_keyword_values),
                self._dump(result.missing_keyword_values),
                int(result.matched_keywords or 0),
                int(result.total_keywords or 0),
                float(result.skill_score or 0.0),
                float(result.experience_score or 0.0),
                float(result.education_score or 0.0),
                float(result.certification_score or 0.0),
                float(result.keyword_score or 0.0),
                self._dump(result.weighted_score_breakdown),
                float(result.overall_match_percentage or 0.0),
                int(result.rank or 0),
                result.recommendation,
                int(bool(result.shortlisted)),
                result.status,
                self._dump(result.remarks),
                processed_time_value,
            ),
        )
        if commit:
            self.db.connection.commit()
        return int(cursor.lastrowid)

    def get_session(self, session_id: int) -> dict[str, Any] | None:
        row = self.db.connection.execute(
            """
            SELECT * FROM screening_sessions
            WHERE id = ? AND tenant_id = ? AND created_by_user_id = ?
            """,
            (int(session_id), self.context.tenant_id, self.context.user_id),
        ).fetchone()
        return dict(row) if row else None

    def list_sessions(self, project_id: int | None = None) -> list[dict[str, Any]]:
        parameters: list[Any] = [self.context.tenant_id, self.context.user_id]
        project_clause = ""
        if project_id is not None:
            project_clause = "AND s.project_id = ?"
            parameters.append(int(project_id))

        rows = self.db.connection.execute(
            f"""
            SELECT s.*, p.project_name, p.job_title, p.client_name
            FROM screening_sessions s
            JOIN recruitment_projects p
              ON p.id = s.project_id
             AND p.tenant_id = s.tenant_id
             AND p.owner_user_id = s.created_by_user_id
            WHERE s.tenant_id = ? AND s.created_by_user_id = ?
              {project_clause}
            ORDER BY s.created_at DESC, s.id DESC
            """,
            tuple(parameters),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_match_results(self, session_id: int) -> list[MatchResult]:
        rows = self.db.connection.execute(
            """
            SELECT m.*, c.full_name, c.email, c.phone, c.source_file,
                   c.candidate_key
            FROM match_results m
            JOIN candidates c
              ON c.id = m.candidate_id
             AND c.tenant_id = m.tenant_id
             AND c.created_by_user_id = m.created_by_user_id
            WHERE m.session_id = ?
              AND m.tenant_id = ?
              AND m.created_by_user_id = ?
            ORDER BY m.rank ASC, m.id ASC
            """,
            (int(session_id), self.context.tenant_id, self.context.user_id),
        ).fetchall()
        return [self.row_to_match_result(row) for row in rows]

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

    def _matching_scope_is_owned(
        self,
        project_id: int,
        session_id: int,
        candidate_id: int,
    ) -> bool:
        row = self.db.connection.execute(
            """
            SELECT 1
            FROM recruitment_projects p
            JOIN screening_sessions s
              ON s.project_id = p.id
             AND s.tenant_id = p.tenant_id
             AND s.created_by_user_id = p.owner_user_id
            JOIN candidates c
              ON c.project_id = p.id
             AND c.session_id = s.id
             AND c.tenant_id = p.tenant_id
             AND c.created_by_user_id = p.owner_user_id
            WHERE p.id = ? AND s.id = ? AND c.id = ?
              AND p.tenant_id = ? AND p.owner_user_id = ?
            """,
            (
                int(project_id),
                int(session_id),
                int(candidate_id),
                self.context.tenant_id,
                self.context.user_id,
            ),
        ).fetchone()
        return row is not None

    @classmethod
    def row_to_match_result(cls, row: Any) -> MatchResult:
        data = dict(row)
        processed_time_raw = str(data.get("processed_time") or "")
        try:
            processed_time = datetime.fromisoformat(processed_time_raw)
        except ValueError:
            processed_time = datetime.now(timezone.utc)

        return MatchResult(
            candidate_id=str(data.get("candidate_key") or data.get("candidate_id") or ""),
            candidate_name=str(data.get("full_name") or ""),
            email=str(data.get("email") or ""),
            phone=str(data.get("phone") or ""),
            source_file=str(data.get("source_file") or ""),
            job_id=str(data.get("job_id") or ""),
            job_title=str(data.get("job_title") or ""),
            matched_skills=cls._load(data.get("matched_skills_json"), []),
            missing_skills=cls._load(data.get("missing_skills_json"), []),
            matched_preferred_skills=cls._load(
                data.get("matched_preferred_skills_json"), []
            ),
            missing_preferred_skills=cls._load(
                data.get("missing_preferred_skills_json"), []
            ),
            additional_skills=cls._load(data.get("additional_skills_json"), []),
            matched_certifications=cls._load(
                data.get("matched_certifications_json"), []
            ),
            missing_certifications=cls._load(
                data.get("missing_certifications_json"), []
            ),
            certification_match=bool(data.get("certification_match")),
            education_match=bool(data.get("education_match")),
            required_experience=float(data.get("required_experience") or 0.0),
            maximum_experience=float(data.get("maximum_experience") or 0.0),
            candidate_experience=float(data.get("candidate_experience") or 0.0),
            experience_match=bool(data.get("experience_match")),
            matched_keyword_values=cls._load(
                data.get("matched_keyword_values_json"), []
            ),
            missing_keyword_values=cls._load(
                data.get("missing_keyword_values_json"), []
            ),
            matched_keywords=int(data.get("matched_keywords") or 0),
            total_keywords=int(data.get("total_keywords") or 0),
            skill_score=float(data.get("skill_score") or 0.0),
            experience_score=float(data.get("experience_score") or 0.0),
            education_score=float(data.get("education_score") or 0.0),
            certification_score=float(data.get("certification_score") or 0.0),
            keyword_score=float(data.get("keyword_score") or 0.0),
            weighted_score_breakdown=cls._load(
                data.get("weighted_score_breakdown_json"), {}
            ),
            overall_match_percentage=float(
                data.get("overall_match_percentage") or 0.0
            ),
            rank=int(data.get("rank") or 0),
            recommendation=str(data.get("recommendation") or ""),
            shortlisted=bool(data.get("shortlisted")),
            status=str(data.get("status") or "Pending"),
            remarks=cls._load(data.get("remarks_json"), []),
            processed_time=processed_time,
        )

    @staticmethod
    def _dump(value: Any) -> str:
        return json.dumps(value if value is not None else [], ensure_ascii=False)

    @staticmethod
    def _load(value: Any, default: Any) -> Any:
        try:
            return json.loads(str(value or ""))
        except (TypeError, ValueError, json.JSONDecodeError):
            return default

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")
