"""Standard result contract for candidate-to-job matching."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MatchResult:
    candidate_id: str = ""
    candidate_name: str = ""
    email: str = ""
    phone: str = ""
    source_file: str = ""

    job_id: str = ""
    job_title: str = ""

    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    matched_preferred_skills: list[str] = field(default_factory=list)
    missing_preferred_skills: list[str] = field(default_factory=list)
    additional_skills: list[str] = field(default_factory=list)

    matched_certifications: list[str] = field(default_factory=list)
    missing_certifications: list[str] = field(default_factory=list)
    certification_match: bool = False
    education_match: bool = False

    required_experience: float = 0.0
    maximum_experience: float = 0.0
    candidate_experience: float = 0.0
    experience_match: bool = False

    matched_keyword_values: list[str] = field(default_factory=list)
    missing_keyword_values: list[str] = field(default_factory=list)
    matched_keywords: int = 0
    total_keywords: int = 0

    skill_score: float = 0.0
    experience_score: float = 0.0
    education_score: float = 0.0
    certification_score: float = 0.0
    keyword_score: float = 0.0
    weighted_score_breakdown: dict[str, float] = field(default_factory=dict)
    overall_match_percentage: float = 0.0

    rank: int = 0
    recommendation: str = ""
    shortlisted: bool = False
    status: str = "Pending"
    remarks: list[str] = field(default_factory=list)
    processed_time: datetime = field(default_factory=datetime.now)

    def total_matched_skills(self) -> int:
        return len(self.matched_skills)

    def total_missing_skills(self) -> int:
        return len(self.missing_skills)

    def total_additional_skills(self) -> int:
        return len(self.additional_skills)

    def total_matched_certifications(self) -> int:
        return len(self.matched_certifications)

    def total_missing_certifications(self) -> int:
        return len(self.missing_certifications)

    def is_shortlisted(self) -> bool:
        return bool(self.shortlisted)

    def add_remark(self, remark: str) -> None:
        cleaned = str(remark or "").strip()
        if cleaned and cleaned not in self.remarks:
            self.remarks.append(cleaned)

    def summary(self) -> dict:
        return {
            "Rank": self.rank,
            "Candidate": self.candidate_name,
            "Job Title": self.job_title,
            "Overall Match %": round(self.overall_match_percentage, 2),
            "Skill Score": round(self.skill_score, 2),
            "Experience Score": round(self.experience_score, 2),
            "Education Score": round(self.education_score, 2),
            "Certification Score": round(self.certification_score, 2),
            "Keyword Score": round(self.keyword_score, 2),
            "Matched Skills": self.total_matched_skills(),
            "Missing Skills": self.total_missing_skills(),
            "Recommendation": self.recommendation,
            "Shortlisted": self.shortlisted,
            "Status": self.status,
        }
