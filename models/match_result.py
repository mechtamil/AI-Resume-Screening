"""
============================================================
RecruitOS
Candidate Match Result Model

Version : 1.0
Author  : Tamilvanan A

Description:
Represents the outcome of comparing one candidate
against a Job Description.

This model is consumed by:

• Matching Engine
• Scoring Engine
• Ranking Engine
• Recommendation Engine
• Results Screen
• Reports
============================================================
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class MatchResult:
    """
    Stores the complete candidate matching result.
    """

    # ---------------------------------------
    # Candidate Information
    # ---------------------------------------

    candidate_name: str = ""

    email: str = ""

    phone: str = ""

    # ---------------------------------------
    # Skill Matching
    # ---------------------------------------

    matched_skills: List[str] = field(default_factory=list)

    missing_skills: List[str] = field(default_factory=list)

    additional_skills: List[str] = field(default_factory=list)

    # ---------------------------------------
    # Education
    # ---------------------------------------

    education_match: bool = False

    # ---------------------------------------
    # Certification
    # ---------------------------------------

    certification_match: bool = False

    # ---------------------------------------
    # Experience
    # ---------------------------------------

    required_experience: float = 0.0

    candidate_experience: float = 0.0

    experience_match: bool = False

    # ---------------------------------------
    # Scores
    # ---------------------------------------

    skill_match_percentage: float = 0.0

    overall_match_percentage: float = 0.0

    # ---------------------------------------
    # Recommendation
    # ---------------------------------------

    recommendation: str = "Review"

    remarks: str = ""

    # ---------------------------------------
    # Helper Methods
    # ---------------------------------------

    def total_matched_skills(self) -> int:
        return len(self.matched_skills)

    def total_missing_skills(self) -> int:
        return len(self.missing_skills)

    def total_additional_skills(self) -> int:
        return len(self.additional_skills)

    def is_shortlisted(self) -> bool:
        """
        Candidate is shortlisted when
        overall score >= 70%.
        """

        return self.overall_match_percentage >= 70

    def summary(self) -> dict:
        """
        Returns a summary dictionary.
        """

        return {

            "Candidate": self.candidate_name,

            "Matched Skills": self.total_matched_skills(),

            "Missing Skills": self.total_missing_skills(),

            "Additional Skills": self.total_additional_skills(),

            "Skill Match %": round(
                self.skill_match_percentage,
                2
            ),

            "Overall Match %": round(
                self.overall_match_percentage,
                2
            ),

            "Recommendation": self.recommendation
        }

    def display(self):

        print("\n========== Match Result ==========")

        print(f"Candidate              : {self.candidate_name}")

        print(f"Matched Skills         : {self.total_matched_skills()}")

        print(f"Missing Skills         : {self.total_missing_skills()}")

        print(f"Additional Skills      : {self.total_additional_skills()}")

        print(f"Skill Match            : {self.skill_match_percentage:.2f}%")

        print(f"Overall Match          : {self.overall_match_percentage:.2f}%")

        print(f"Recommendation         : {self.recommendation}")

        print("===================================")