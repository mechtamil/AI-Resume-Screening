"""
============================================================
RecruitOS
Enterprise Match Result Model

Version : 2.0
Author  : Tamilvanan A

Description:
Represents the complete outcome of matching a
Candidate against a Job Description.

This model is the standard data contract between:

• Matching Engine
• AI Recommendation Engine
• Ranking Engine
• Dashboard
• Analytics
• Reports
• Export Engine
============================================================
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class MatchResult:
    """
    Enterprise Candidate Match Result.
    """

    # =====================================================
    # Candidate Information
    # =====================================================

    candidate_id: str = ""

    candidate_name: str = ""

    email: str = ""

    phone: str = ""

    source_file: str = ""

    # =====================================================
    # Job Information
    # =====================================================

    job_id: str = ""

    job_title: str = ""

    # =====================================================
    # Skill Matching
    # =====================================================

    matched_skills: List[str] = field(default_factory=list)

    missing_skills: List[str] = field(default_factory=list)

    additional_skills: List[str] = field(default_factory=list)

    # =====================================================
    # Certification Matching
    # =====================================================

    matched_certifications: List[str] = field(default_factory=list)

    missing_certifications: List[str] = field(default_factory=list)

    # =====================================================
    # Education
    # =====================================================

    education_match: bool = False

    # =====================================================
    # Experience
    # =====================================================

    required_experience: float = 0.0

    candidate_experience: float = 0.0

    experience_match: bool = False

    # =====================================================
    # Keyword Statistics
    # =====================================================

    matched_keywords: int = 0

    total_keywords: int = 0

    # =====================================================
    # Individual Scores
    # =====================================================

    skill_score: float = 0.0

    experience_score: float = 0.0

    education_score: float = 0.0

    certification_score: float = 0.0

    keyword_score: float = 0.0

    # =====================================================
    # Overall Result
    # =====================================================

    overall_match_percentage: float = 0.0

    rank: int = 0

    recommendation: str = "Review"

    status: str = "Pending"

    # =====================================================
    # AI Explanation
    # =====================================================

    remarks: List[str] = field(default_factory=list)

    # =====================================================
    # Audit Information
    # =====================================================

    processed_time: datetime = field(
        default_factory=datetime.now
    )

    # =====================================================
    # Helper Methods
    # =====================================================

    def total_matched_skills(self):

        return len(self.matched_skills)

    def total_missing_skills(self):

        return len(self.missing_skills)

    def total_additional_skills(self):

        return len(self.additional_skills)

    def total_matched_certifications(self):

        return len(self.matched_certifications)

    def total_missing_certifications(self):

        return len(self.missing_certifications)

    def is_shortlisted(self):

        return self.overall_match_percentage >= 70

    def add_remark(self, remark: str):

        if remark:

            self.remarks.append(remark)

    # =====================================================
    # Summary
    # =====================================================

    def summary(self):

        return {

            "Candidate": self.candidate_name,

            "Job Title": self.job_title,

            "Overall Match %": round(
                self.overall_match_percentage,
                2
            ),

            "Skill Score": round(
                self.skill_score,
                2
            ),

            "Experience Score": round(
                self.experience_score,
                2
            ),

            "Education Score": round(
                self.education_score,
                2
            ),

            "Certification Score": round(
                self.certification_score,
                2
            ),

            "Keyword Score": round(
                self.keyword_score,
                2
            ),

            "Matched Skills": self.total_matched_skills(),

            "Missing Skills": self.total_missing_skills(),

            "Recommendation": self.recommendation,

            "Rank": self.rank,

            "Status": self.status

        }

    # =====================================================
    # Display
    # =====================================================

    def display(self):

        print("\n================ MATCH RESULT ================")

        print(f"Candidate           : {self.candidate_name}")

        print(f"Job Title           : {self.job_title}")

        print(f"Overall Match       : {self.overall_match_percentage:.2f}%")

        print()

        print(f"Skill Score         : {self.skill_score:.2f}%")

        print(f"Experience Score    : {self.experience_score:.2f}%")

        print(f"Education Score     : {self.education_score:.2f}%")

        print(f"Certification Score : {self.certification_score:.2f}%")

        print(f"Keyword Score       : {self.keyword_score:.2f}%")

        print()

        print(f"Matched Skills      : {self.total_matched_skills()}")

        print(f"Missing Skills      : {self.total_missing_skills()}")

        print(f"Additional Skills   : {self.total_additional_skills()}")

        print()

        print(f"Recommendation      : {self.recommendation}")

        print(f"Rank                : {self.rank}")

        print(f"Status              : {self.status}")

        print()

        if self.remarks:

            print("Remarks")

            for remark in self.remarks:

                print(f" • {remark}")

        print("\n==============================================")