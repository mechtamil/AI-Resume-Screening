"""End-to-end RecruitOS screening workflow orchestration."""
from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path
from typing import Any

from JD.jd_parser import JDParser
from models.security_context import SecurityContext
from parser.resume_parser import ResumeParser
from services.configuration_context import ConfigurationContext
from services.configuration_validator import ConfigurationValidator
from services.document_manager import DocumentManager
from services.matching.matching_orchestrator import MatchingOrchestrator
from services.skill_list_service import SkillListService
from services.tenant_configuration_service import TenantConfigurationService


class ProcessingService:
    @staticmethod
    def _merge_skills(existing: list[str], supplemental: list[str]) -> list[str]:
        output: list[str] = []
        seen: set[str] = set()
        for value in [*(existing or []), *(supplemental or [])]:
            cleaned = str(value or "").strip()
            key = cleaned.casefold()
            if cleaned and key not in seen:
                seen.add(key)
                output.append(cleaned)
        return output

    @classmethod
    def process_documents(
        cls,
        jd_path: str | Path,
        resume_paths: list[str | Path],
        skill_list_path: str | Path | None = None,
        job_id: str = "",
        *,
        security_context: SecurityContext | None = None,
        configuration_service: TenantConfigurationService | None = None,
    ) -> dict[str, Any]:
        """Process documents using one immutable configuration selection.

        Authenticated web requests resolve the active tenant configuration and
        keep it in a context-local scope for the complete parse/match operation.
        Command-line and legacy tests continue to use the system-default workbook.
        """
        configuration_snapshot: dict[str, Any] = {}
        context_manager = nullcontext()

        if security_context is not None:
            security_context.require_valid()
            service = configuration_service or TenantConfigurationService()
            selection, configuration_snapshot = service.snapshot_for_screening(
                security_context
            )
            context_manager = ConfigurationContext.activate(selection)

        with context_manager:
            validation = ConfigurationValidator.validate_or_raise()
            jd_document = DocumentManager.read_document(jd_path)
            job = JDParser.parse(jd_document)

            if skill_list_path:
                supplemental = SkillListService.read_skills(skill_list_path)
                job.mandatory_skills = cls._merge_skills(
                    job.mandatory_skills,
                    supplemental,
                )

            candidates = []
            errors: list[dict[str, str]] = []
            for resume_path in resume_paths or []:
                try:
                    document = DocumentManager.read_document(resume_path)
                    candidates.append(ResumeParser.parse(document))
                except Exception as exc:
                    errors.append({"file": Path(resume_path).name, "error": str(exc)})

            orchestrator = MatchingOrchestrator()
            match_results = orchestrator.match_many(job, candidates, job_id=job_id)

        if not configuration_snapshot:
            configuration_snapshot = {
                "source": "system_default",
                "version_id": None,
                "version_number": None,
                "configuration_key": "system-default",
                "sha256": str(validation.get("sha256") or ""),
                "file_size": Path(validation["workbook_path"]).stat().st_size,
                "activated_at": "",
                "sheet_summary": dict(validation.get("sheets") or {}),
                "validation": {
                    "valid": True,
                    "warnings": list(validation.get("warnings") or []),
                },
            }

        return {
            "job_description": job,
            "candidates": candidates,
            "match_results": match_results,
            "errors": errors,
            "configuration": configuration_snapshot,
            "summary": {
                "resumes_requested": len(resume_paths or []),
                "resumes_processed": len(candidates),
                "resumes_failed": len(errors),
            },
        }
