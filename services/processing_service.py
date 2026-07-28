"""End-to-end RecruitOS screening workflow orchestration."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from JD.jd_parser import JDParser
from parser.resume_parser import ResumeParser
from services.configuration_validator import ConfigurationValidator
from services.document_manager import DocumentManager
from services.matching.matching_orchestrator import MatchingOrchestrator
from services.skill_list_service import SkillListService


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
    ) -> dict[str, Any]:
        ConfigurationValidator.validate_or_raise()
        jd_document = DocumentManager.read_document(jd_path)
        job = JDParser.parse(jd_document)

        if skill_list_path:
            supplemental = SkillListService.read_skills(skill_list_path)
            job.mandatory_skills = cls._merge_skills(job.mandatory_skills, supplemental)

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

        return {
            "job_description": job,
            "candidates": candidates,
            "match_results": match_results,
            "errors": errors,
            "summary": {
                "resumes_requested": len(resume_paths or []),
                "resumes_processed": len(candidates),
                "resumes_failed": len(errors),
            },
        }
