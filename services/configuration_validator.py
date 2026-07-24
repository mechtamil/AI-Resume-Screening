"""Preflight validation for RecruitOS configuration before screening."""
from __future__ import annotations

from config.settings import VERSION
from services.certification_repository import CertificationRepository
from services.configuration_repository import ConfigurationRepository
from services.education_repository import EducationRepository
from services.master_repository import MasterRepository
from services.recommendation_repository import RecommendationRepository
from services.scoring_repository import ScoringRepository
from services.skill_repository import SkillRepository


class ConfigurationValidator:
    @classmethod
    def validate(cls) -> dict:
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
                errors.append(f"Active scoring weights total {scoring.get_total_weight():g}; expected 100.")
            if not recommendations.validate_coverage(0, 100):
                errors.append("Recommendation ranges must continuously cover 0 through 100.")
            if skills.total_skills() == 0:
                warnings.append("Skills sheet has no active master data.")
            if education.total_degrees() == 0:
                warnings.append("Education sheet has no active master data.")
            if certifications.total_certifications() == 0:
                warnings.append("Certifications sheet has no active master data.")

            workbook_version = str(configuration.get("Version", "") or "").strip()
            if workbook_version and workbook_version != VERSION:
                warnings.append(
                    f"Configuration workbook version '{workbook_version}' differs from application version '{VERSION}'."
                )
        except Exception as exc:
            errors.append(str(exc))

        return {"valid": not errors, "errors": errors, "warnings": warnings}

    @classmethod
    def validate_or_raise(cls) -> dict:
        report = cls.validate()
        if not report["valid"]:
            raise ValueError("Invalid RecruitOS configuration:\n- " + "\n- ".join(report["errors"]))
        return report
