"""
============================================================
RecruitOS
Enterprise Experience Matcher

Version : 1.0
Author  : Tamilvanan A

Description:
Compares Candidate experience with the Job Description
experience requirements.

Responsibilities:
    • Compare experience
    • Calculate experience score
    • Update MatchResult
    • Generate AI remarks
============================================================
"""

from models.candidate import Candidate
from JD.jd_model import JobDescription
from models.match_result import MatchResult


class ExperienceMatcher:
    """
    Enterprise Experience Matcher.
    """

    @staticmethod
    def match(
        candidate: Candidate,
        job: JobDescription,
        result: MatchResult
    ) -> MatchResult:

        result.candidate_experience = (
            candidate.total_experience
        )

        result.required_experience = (
            job.experience_min
        )

        # ----------------------------------------
        # No experience requirement
        # ----------------------------------------

        if job.experience_min <= 0:

            result.experience_match = True

            result.experience_score = 100

            result.add_remark(
                "No minimum experience specified."
            )

            return result

        # ----------------------------------------
        # Candidate meets requirement
        # ----------------------------------------

        if candidate.total_experience >= job.experience_min:

            result.experience_match = True

            result.experience_score = 100

            difference = round(

                candidate.total_experience
                - job.experience_min,

                2

            )

            if difference == 0:

                result.add_remark(
                    "Candidate exactly meets the required experience."
                )

            else:

                result.add_remark(
                    f"Candidate exceeds the required experience by {difference} years."
                )

        # ----------------------------------------
        # Candidate below requirement
        # ----------------------------------------

        else:

            result.experience_match = False

            score = (

                candidate.total_experience
                / job.experience_min

            ) * 100

            result.experience_score = round(

                min(score, 100),

                2

            )

            shortage = round(

                job.experience_min
                - candidate.total_experience,

                2

            )

            result.add_remark(
                f"Candidate is below the required experience by {shortage} years."
            )

        return result