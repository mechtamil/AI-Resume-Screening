"""Private persistence orchestration for RecruitOS screening projects."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any
from uuid import uuid4

from JD.jd_model import JobDescription
from database.candidate_repository import CandidateRepository
from database.database import Database
from database.project_repository import ProjectRepository
from database.screening_repository import ScreeningRepository
from models.candidate import Candidate
from models.recruitment_project import RecruitmentProject
from models.security_context import SecurityContext
from models.storage_asset import StorageScope
from services.secure_storage_service import SecureStorageService


class PersistenceService:
    """Save and reconstruct screening sessions in the current private workspace."""

    @classmethod
    def save_analysis_result(
        cls,
        context: SecurityContext,
        analysis_result: dict[str, Any],
        database_path: str | Path | None = None,
    ) -> dict[str, Any]:
        context.require_valid()
        if not isinstance(analysis_result, dict):
            raise TypeError("analysis_result must be a dictionary.")

        job = analysis_result.get("job_description")
        if not isinstance(job, JobDescription):
            raise ValueError("analysis_result must contain a JobDescription.")

        candidates = list(analysis_result.get("candidates") or [])
        matches = list(analysis_result.get("match_results") or [])
        summary = dict(analysis_result.get("summary") or {})
        errors = list(analysis_result.get("errors") or [])
        project_data = dict(analysis_result.get("project") or {})
        configuration_data = dict(analysis_result.get("configuration") or {})

        project = RecruitmentProject(
            project_name=str(
                project_data.get("project_name")
                or job.job_title
                or "RecruitOS Screening Project"
            ),
            client_name=str(project_data.get("client_name") or job.company_name or ""),
            job_title=job.job_title,
            hiring_manager=str(project_data.get("hiring_manager") or ""),
            location=job.location,
            target_headcount=int(project_data.get("target_headcount") or 0),
            uploaded_resumes=int(summary.get("resumes_requested") or len(candidates)),
            processed_resumes=int(summary.get("resumes_processed") or len(candidates)),
            shortlisted=sum(1 for item in matches if bool(item.shortlisted)),
            rejected=sum(1 for item in matches if not bool(item.shortlisted)),
            status=str(project_data.get("status") or "Open"),
        )

        match_job_id = str(matches[0].job_id or "") if matches else ""
        job_id = str(project_data.get("job_id") or match_job_id or "")
        explicit_key = str(project_data.get("project_key") or "").strip()
        project_key = explicit_key or (f"job:{job_id}" if job_id else uuid4().hex)
        storage_data = dict(analysis_result.get("storage") or {})
        requested_workspace = str(storage_data.get("workspace_id") or "").strip().lower()
        if requested_workspace:
            StorageScope(
                tenant_id=context.tenant_id,
                user_id=context.user_id,
                workspace_id=requested_workspace,
            ).require_valid()
        session_key = requested_workspace or uuid4().hex

        database = Database(database_path)
        database.create_tables()
        projects = ProjectRepository(context, database)
        candidate_repository = CandidateRepository(context, database)
        screenings = ScreeningRepository(context, database)

        try:
            with database.transaction():
                project_id = projects.upsert_project(
                    project,
                    project_key=project_key,
                    job_id=job_id,
                    job_description=asdict(job),
                    commit=False,
                )

                session_summary = dict(summary)
                session_summary["shortlisted_count"] = project.shortlisted
                session_id = screenings.create_session(
                    project_id,
                    summary=session_summary,
                    errors=errors,
                    session_key=session_key,
                    configuration=configuration_data,
                    commit=False,
                )

                candidate_ids: dict[int, int] = {}
                for index, candidate in enumerate(candidates):
                    if not isinstance(candidate, Candidate):
                        raise ValueError("All candidates must be Candidate objects.")
                    candidate_id = candidate_repository.add_candidate_model(
                        candidate,
                        project_id=project_id,
                        session_id=session_id,
                        candidate_key=uuid4().hex,
                        status="Processed",
                        commit=False,
                    )
                    candidate_ids[index] = candidate_id

                matches_saved = 0
                used_candidate_ids: set[int] = set()
                for result in matches:
                    candidate_id = cls._find_candidate_id(
                        result,
                        candidates,
                        candidate_ids,
                        used_candidate_ids,
                    )
                    if candidate_id is None:
                        continue
                    screenings.add_match_result(
                        result,
                        project_id=project_id,
                        session_id=session_id,
                        candidate_id=candidate_id,
                        commit=False,
                    )
                    used_candidate_ids.add(candidate_id)
                    matches_saved += 1

            persistence = {
                "tenant_id": context.tenant_id,
                "owner_user_id": context.user_id,
                "project_id": project_id,
                "project_key": project_key,
                "session_id": session_id,
                "session_key": session_key,
                "candidates_saved": len(candidates),
                "matches_saved": matches_saved,
            }
            analysis_result["persistence"] = persistence
            analysis_result["storage"] = {
                **storage_data,
                "tenant_id": context.tenant_id,
                "user_id": context.user_id,
                "workspace_id": session_key,
            }
            analysis_result.setdefault("project", {})["project_key"] = project_key
            return persistence
        finally:
            database.close()

    @classmethod
    def load_session(
        cls,
        context: SecurityContext,
        session_id: int,
        database_path: str | Path | None = None,
    ) -> dict[str, Any]:
        context.require_valid()
        database = Database(database_path)
        database.create_tables()
        projects = ProjectRepository(context, database)
        candidates = CandidateRepository(context, database)
        screenings = ScreeningRepository(context, database)

        try:
            session = screenings.get_session(session_id)
            if not session:
                raise LookupError("The requested screening session is not available.")

            project = projects.get_project(int(session["project_id"]))
            if not project:
                raise LookupError("The requested screening project is not available.")

            job_payload = cls._load_json(project.get("jd_json"), {})
            job = JobDescription(
                **{
                    key: value
                    for key, value in job_payload.items()
                    if key in JobDescription.__dataclass_fields__
                }
            )
            candidate_models = candidates.list_candidates(session_id=int(session_id))
            match_results = screenings.get_match_results(int(session_id))
            errors = cls._load_json(session.get("errors_json"), [])
            configuration = cls._load_json(
                session.get("configuration_snapshot_json"),
                {},
            )
            if not configuration and str(session.get("configuration_sha256") or ""):
                configuration = {
                    "version_id": session.get("configuration_version_id"),
                    "sha256": str(session.get("configuration_sha256") or ""),
                }

            return {
                "job_description": job,
                "candidates": candidate_models,
                "match_results": match_results,
                "errors": errors,
                "configuration": configuration,
                "summary": {
                    "resumes_requested": int(session.get("resumes_requested") or 0),
                    "resumes_processed": int(session.get("resumes_processed") or 0),
                    "resumes_failed": int(session.get("resumes_failed") or 0),
                    "shortlisted_count": int(session.get("shortlisted_count") or 0),
                },
                "project": {
                    "project_id": int(project["id"]),
                    "project_key": str(project.get("project_key") or ""),
                    "project_name": str(project.get("project_name") or ""),
                    "client_name": str(project.get("client_name") or ""),
                    "hiring_manager": str(project.get("hiring_manager") or ""),
                    "job_id": str(project.get("job_id") or ""),
                    "target_headcount": int(project.get("target_headcount") or 0),
                    "status": str(project.get("status") or "Open"),
                },
                "storage": {
                    "tenant_id": context.tenant_id,
                    "user_id": context.user_id,
                    "workspace_id": str(session.get("session_key") or ""),
                },
                "persistence": {
                    "tenant_id": context.tenant_id,
                    "owner_user_id": context.user_id,
                    "project_id": int(project["id"]),
                    "project_key": str(project.get("project_key") or ""),
                    "session_id": int(session["id"]),
                    "session_key": str(session.get("session_key") or ""),
                    "reopened": True,
                },
            }
        finally:
            database.close()

    @staticmethod
    def list_projects(
        context: SecurityContext,
        database_path: str | Path | None = None,
    ) -> list[dict[str, Any]]:
        repository = ProjectRepository(context, database_path)
        try:
            return repository.list_projects()
        finally:
            repository.close()

    @staticmethod
    def list_sessions(
        context: SecurityContext,
        project_id: int | None = None,
        database_path: str | Path | None = None,
    ) -> list[dict[str, Any]]:
        repository = ScreeningRepository(context, database_path)
        try:
            return repository.list_sessions(project_id)
        finally:
            repository.close()

    @staticmethod
    def list_candidate_records(
        context: SecurityContext,
        *,
        project_id: int | None = None,
        session_id: int | None = None,
        database_path: str | Path | None = None,
    ) -> list[dict[str, Any]]:
        repository = CandidateRepository(context, database_path)
        try:
            return repository.list_candidate_records(
                project_id=project_id,
                session_id=session_id,
            )
        finally:
            repository.close()

    @staticmethod
    def delete_project(
        context: SecurityContext,
        project_id: int,
        database_path: str | Path | None = None,
        storage: SecureStorageService | None = None,
    ) -> bool:
        """Delete an owned project and then remove only its private file workspaces."""
        context.require_valid()
        database = Database(database_path)
        database.create_tables()
        projects = ProjectRepository(context, database)
        screenings = ScreeningRepository(context, database)
        try:
            sessions = screenings.list_sessions(int(project_id))
            deleted = projects.delete_project(int(project_id))
        finally:
            database.close()

        if deleted:
            private_storage = storage or SecureStorageService()
            for session in sessions:
                workspace_id = str(session.get("session_key") or "").strip().lower()
                if not workspace_id:
                    continue
                try:
                    scope = StorageScope(
                        tenant_id=context.tenant_id,
                        user_id=context.user_id,
                        workspace_id=workspace_id,
                    )
                    scope.require_valid()
                    private_storage.delete_workspace(context, scope)
                except (OSError, PermissionError, ValueError):
                    # Database ownership is already removed. A later retention sweep may
                    # delete an unavailable/orphaned filesystem workspace safely.
                    continue
        return deleted

    @staticmethod
    def _find_candidate_id(result, candidates, candidate_ids, used_ids) -> int | None:
        result_values = {
            str(getattr(result, "source_file", "") or "").casefold(),
            str(getattr(result, "email", "") or "").casefold(),
            str(getattr(result, "candidate_name", "") or "").casefold(),
        }
        result_values.discard("")

        for index, candidate in enumerate(candidates):
            candidate_id = candidate_ids[index]
            if candidate_id in used_ids:
                continue
            candidate_values = {
                str(candidate.source_file or "").casefold(),
                str(candidate.email or "").casefold(),
                str(candidate.full_name or "").casefold(),
            }
            candidate_values.discard("")
            if result_values.intersection(candidate_values):
                return candidate_id

        for index in range(len(candidates)):
            candidate_id = candidate_ids[index]
            if candidate_id not in used_ids:
                return candidate_id
        return None

    @staticmethod
    def _load_json(value: Any, default: Any) -> Any:
        try:
            return json.loads(str(value or ""))
        except (TypeError, ValueError, json.JSONDecodeError):
            return default
