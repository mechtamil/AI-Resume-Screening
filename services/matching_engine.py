"""
============================================================
RecruitOS
Candidate Matching Engine

Version : 1.0
Author  : Tamilvanan A

Description:
Compares a parsed Job Description against a parsed
Candidate Resume and produces a MatchResult.

This service is responsible ONLY for comparison logic.

It does NOT:
✓ Read documents
✓ Parse resumes
✓ Parse Job Descriptions
✓ Handle UI

============================================================
"""

from typing import Set

from JD.jd_model import JobDescription
from models.match_result import MatchResult


class MatchingEngine:
    """
    Performs candidate matching against
    a Job Description.
    """

    @staticmethod
    def _normalize(items) -> Set[str]:
        """
        Normalize list values.

        - Remove None
        - Remove blanks
        - Strip spaces
        - Lowercase
        - Remove duplicates
        """

        if not items:
            return set()

        normalized = set()

        for item in items:

            if item is None:
                continue

            value = str(item).strip().lower()

            if value:
                normalized.add(value)

        return normalized

    @staticmethod
    def match(
        job_description: JobDescription,
        candidate
    ) -> MatchResult:
        """
        Compare one candidate with one Job Description.
        """

        result = MatchResult()

        # -------------------------------------------------
        # Candidate Information
        # -------------------------------------------------

        result.candidate_name = getattr(
            candidate,
            "full_name",
            ""
        )

        result.email = getattr(
            candidate,
            "email",
            ""
        )

        result.phone = getattr(
            candidate,
            "phone",
            ""
        )

        # -------------------------------------------------
        # Skills
        # -------------------------------------------------

        jd_skills = MatchingEngine._normalize(
            job_description.mandatory_skills
        )

        candidate_skills = MatchingEngine._normalize(
            getattr(candidate, "technical_skills", [])
        )

        matched = jd_skills.intersection(
            candidate_skills
        )

        missing = jd_skills.difference(
            candidate_skills
        )

        additional = candidate_skills.difference(
            jd_skills
        )

        result.matched_skills = sorted(list(matched))

        result.missing_skills = sorted(list(missing))

        result.additional_skills = sorted(list(additional))

        # -------------------------------------------------
        # Skill Percentage
        # -------------------------------------------------

        if len(jd_skills) > 0:

            result.skill_match_percentage = round(

                (len(matched) / len(jd_skills)) * 100,

                2

            )

        else:

            result.skill_match_percentage = 100.0

        # -------------------------------------------------
        # Experience
        # -------------------------------------------------

        required = job_description.experience_min

        candidate_exp = getattr(
            candidate,
            "total_experience",
            0
        )

        try:

            candidate_exp = float(candidate_exp)

        except Exception:

            candidate_exp = 0.0

        result.required_experience = required

        result.candidate_experience = candidate_exp

        result.experience_match = (

            candidate_exp >= required

        )

        # -------------------------------------------------
        # Education
        # -------------------------------------------------

        jd_education = MatchingEngine._normalize(

            job_description.education

        )

        candidate_education = MatchingEngine._normalize(

            getattr(candidate, "education", [])

        )

        if len(jd_education) == 0:

            result.education_match = True

        else:

            result.education_match = (

                len(

                    jd_education.intersection(

                        candidate_education

                    )

                ) > 0

            )

        # -------------------------------------------------
        # Certification
        # -------------------------------------------------

        jd_certifications = MatchingEngine._normalize(

            job_description.certifications

        )

        candidate_certifications = MatchingEngine._normalize(

            getattr(candidate, "certifications", [])

        )

        if len(jd_certifications) == 0:

            result.certification_match = True

        else:

            result.certification_match = (

                len(

                    jd_certifications.intersection(

                        candidate_certifications

                    )

                ) > 0

            )

        # -------------------------------------------------
        # Overall Score
        # (Temporary)
        # -------------------------------------------------

        score = result.skill_match_percentage

        if result.experience_match:
            score += 10

        if result.education_match:
            score += 5

        if result.certification_match:
            score += 5

        if score > 100:
            score = 100

        result.overall_match_percentage = round(score, 2)

        # -------------------------------------------------
        # Recommendation
        # -------------------------------------------------

        if result.overall_match_percentage >= 85:

            result.recommendation = "Strongly Recommended"

        elif result.overall_match_percentage >= 70:

            result.recommendation = "Recommended"

        elif result.overall_match_percentage >= 50:

            result.recommendation = "Consider"

        else:

            result.recommendation = "Not Recommended"

        # -------------------------------------------------
        # Remarks
        # -------------------------------------------------

        result.remarks = (

            f"{len(result.matched_skills)} matched, "

            f"{len(result.missing_skills)} missing skills."

        )

        return result