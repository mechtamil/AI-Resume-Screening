"""
============================================================
RecruitOS
Candidate Model
Version : 1.0
Author  : Tamilvanan A

Description:
Represents a Candidate parsed from a Resume.
============================================================
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Candidate:
    """
    Standard Candidate Model
    """

    # Personal Information
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""

    # Professional Information
    designation: str = ""
    total_experience: float = 0.0

    # Qualification
    education: List[str] = field(default_factory=list)

    certifications: List[str] = field(default_factory=list)

    # Skills
    technical_skills: List[str] = field(default_factory=list)

    soft_skills: List[str] = field(default_factory=list)

    tools: List[str] = field(default_factory=list)

    # Projects
    projects: List[str] = field(default_factory=list)

    # Employment
    companies: List[str] = field(default_factory=list)

    # Resume Metadata
    source_file: str = ""

    raw_text: str = ""

    # ---------- Utility Methods ----------

    def total_skills(self) -> int:
        return (
            len(self.technical_skills)
            + len(self.soft_skills)
            + len(self.tools)
        )

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

            "Certifications": len(self.certifications)

        }