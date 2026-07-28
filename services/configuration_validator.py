"""Preflight validation for system and tenant RecruitOS configurations."""
from __future__ import annotations

from pathlib import Path

from config.settings import VERSION
from models.configuration_version import ConfigurationSelection
from services.certification_repository import CertificationRepository
from services.configuration_context import ConfigurationContext
from services.configuration_repository import ConfigurationRepository
from services.education_repository import EducationRepository
from services.master_repository import MasterRepository
from services.recommendation_repository import RecommendationRepository
from services.scoring_repository import ScoringRepository
from services.skill_repository import SkillRepository


class ConfigurationValidator:
    @classmethod
    def validate(
        cls,
        workbook_path: str | Path | None = None,
    ) -> dict:
        if workbook_path is None:
            return cls._validate_active()

        path = Path(workbook_path).expanduser().resolve()
        selection = ConfigurationSelection(
            tenant_id=0,
            workbook_path=path,
            source="validation",
            configuration_key=f"validation:{path.name}",
            sha256=MasterRepository.workbook_sha256(path) if path.is_file() else "",
            file_size=path.stat().st_size if path.is_file() else 0,
        )
        with ConfigurationContext.activate(selection):
            return cls._validate_active()

    @classmethod
    def _validate_active(cls) -> dict:
        errors: list[str] = []
        warnings: list[str] = []
        try:
            MasterRepository.validate_workbook()
            skills = SkillRepository()
            education = EducationRepository()
            certifications = CertificationRepository()
            scoring = ScoringRepository()
            recommendations = RecommendationRepository()
            configuration = ConfigurationRepository()

            if not scoring.validate_total_weight(100):
                errors.append(
                    f"Active scoring weights total {scoring.get_total_weight():g}; expected 100."
                )
            if not recommendations.validate_coverage(0, 100):
                errors.append(
                    "Recommendation ranges must continuously cover 0 through 100."
                )
            if skills.total_skills() == 0:
                warnings.append("Skills sheet has no active master data.")
            if education.total_degrees() == 0:
                warnings.append("Education sheet has no active master data.")
            if certifications.total_certifications() == 0:
                warnings.append("Certifications sheet has no active master data.")

            workbook_version = str(configuration.get("Version", "") or "").strip()
            if workbook_version and workbook_version != VERSION:
                warnings.append(
                    f"Configuration workbook version '{workbook_version}' differs "
                    f"from application version '{VERSION}'."
                )
        except Exception as exc:
            errors.append(str(exc))

        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
            "workbook_path": str(MasterRepository.active_workbook_path()),
            "sha256": (
                MasterRepository.workbook_sha256()
                if MasterRepository.active_workbook_path().is_file()
                else ""
            ),
            "sheets": (
                MasterRepository.workbook_info()
                if not errors and MasterRepository.active_workbook_path().is_file()
                else {}
            ),
        }

    @classmethod
    def validate_or_raise(
        cls,
        workbook_path: str | Path | None = None,
    ) -> dict:
        report = cls.validate(workbook_path)
        if not report["valid"]:
            raise ValueError(
                "Invalid RecruitOS configuration:\n- "
                + "\n- ".join(report["errors"])
            )
        return report
