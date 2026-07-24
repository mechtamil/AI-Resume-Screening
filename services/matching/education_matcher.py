"""
============================================================
RecruitOS
Enterprise Education Matcher

Version : 1.0
Author  : Tamilvanan A

Description:
Compares Candidate education with Job Description
education requirements.

Responsibilities:
    • Compare education
    • Calculate education score
    • Update MatchResult
    • Generate AI remarks
============================================================
"""

from models.candidate import Candidate
from JD.jd_model import JobDescription
from models.match_result import MatchResult


class EducationMatcher:
    """
    Enterprise Education Matcher.
    """

    @staticmethod
    def match(
        candidate: Candidate,
        job: JobDescription,
        result: MatchResult
    ) -> MatchResult:

        candidate_education = {

            education.strip().lower()

            for education in candidate.education

            if education.strip()

        }

        required_education = {

            education.strip().lower()

            for education in job.education

            if education.strip()

        }

        # ---------------------------------------
        # No education requirement
        # ---------------------------------------

        if not required_education:

            result.education_match = True

            result.education_score = 100

            result.add_remark(
                "No education requirement specified."
            )

            return result

        # ---------------------------------------
        # Education Match
        # ---------------------------------------

        if candidate_education.intersection(
            required_education
        ):

            result.education_match = True

            result.education_score = 100

            result.add_remark(
                "Candidate satisfies the education requirement."
            )

        else:

            result.education_match = False

            result.education_score = 0

            result.add_remark(
                "Candidate does not satisfy the required education."
            )

        return result