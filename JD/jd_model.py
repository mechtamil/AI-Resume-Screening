"""
============================================================
RecruitOS
Job Description Model
Version : 1.0
Author  : Tamilvanan A

Description:
Represents a Job Description in a structured format.
This model is populated by the JD Parser and consumed
by the Matching Engine.
============================================================
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class JobDescription:
    """
    Standard Job Description Model
    """

    job_title: str = ""

    company_name: str = ""

    location: str = ""

    employment_type: str = ""

    experience_min: float = 0.0

    experience_max: float = 0.0

    education: List[str] = field(default_factory=list)

    mandatory_skills: List[str] = field(default_factory=list)

    preferred_skills: List[str] = field(default_factory=list)

    certifications: List[str] = field(default_factory=list)

    responsibilities: List[str] = field(default_factory=list)

    keywords: List[str] = field(default_factory=list)

    notes: str = ""

    source_file: str = ""

    raw_text: str = ""

    def total_required_skills(self) -> int:
        """
        Returns the number of mandatory skills.
        """
        return len(self.mandatory_skills)

    def total_preferred_skills(self) -> int:
        """
        Returns the number of preferred skills.
        """
        return len(self.preferred_skills)

    def total_keywords(self) -> int:
        """
        Returns the number of keywords.
        """
        return len(self.keywords)

    def summary(self) -> dict:
        """
        Returns a summary dictionary for reporting.
        """

        return {
            "Job Title": self.job_title,
            "Company": self.company_name,
            "Location": self.location,
            "Experience": f"{self.experience_min} - {self.experience_max} Years",
            "Mandatory Skills": len(self.mandatory_skills),
            "Preferred Skills": len(self.preferred_skills),
            "Education": ", ".join(self.education),
            "Certifications": len(self.certifications)
        }