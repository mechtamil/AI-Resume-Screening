"""Authoritative JobDescription domain model for RecruitOS."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class JobDescription:
    job_title: str = ""
    company_name: str = ""
    location: str = ""
    employment_type: str = ""
    experience_min: float = 0.0
    experience_max: float = 0.0
    education: list[str] = field(default_factory=list)
    mandatory_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    notes: str = ""
    source_file: str = ""
    raw_text: str = ""

    def total_required_skills(self) -> int:
        return len(self.mandatory_skills)

    def total_preferred_skills(self) -> int:
        return len(self.preferred_skills)

    def total_keywords(self) -> int:
        return len(self.keywords)

    def summary(self) -> dict:
        experience = (
            f"{self.experience_min:g} - {self.experience_max:g} Years"
            if self.experience_max
            else f"{self.experience_min:g} Years"
        )
        return {
            "Job Title": self.job_title,
            "Company": self.company_name,
            "Location": self.location,
            "Experience": experience,
            "Mandatory Skills": len(self.mandatory_skills),
            "Preferred Skills": len(self.preferred_skills),
            "Education": ", ".join(self.education),
            "Certifications": len(self.certifications),
        }
