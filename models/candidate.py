"""RecruitOS candidate domain model."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Candidate:
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    website: str = ""

    designation: str = ""
    total_experience: float = 0.0

    education: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    technical_skills: list[str] = field(default_factory=list)
    soft_skills: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)
    companies: list[str] = field(default_factory=list)

    source_file: str = ""
    raw_text: str = ""

    def total_skills(self) -> int:
        return len(self.technical_skills) + len(self.soft_skills) + len(self.tools)

    def total_projects(self) -> int:
        return len(self.projects)

    def total_certifications(self) -> int:
        return len(self.certifications)

    def summary(self) -> dict:
        return {
            "Candidate": self.full_name,
            "Experience": self.total_experience,
            "Technical Skills": len(self.technical_skills),
            "Tools": len(self.tools),
            "Projects": len(self.projects),
            "Certifications": len(self.certifications),
        }
