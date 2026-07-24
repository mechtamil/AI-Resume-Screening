"""
============================================================
RecruitOS
Enterprise Skill Matcher

Version : 1.0
Author  : Tamilvanan A

Description:
Compares Candidate skills with Job Description skills.

Responsibilities:
    • Identify matched skills
    • Identify missing skills
    • Identify additional skills
    • Calculate skill score
    • Generate AI remarks

Output:
    MatchResult
============================================================
"""

from models.match_result import MatchResult
from models.candidate import Candidate
from JD.jd_model import JobDescription


class SkillMatcher:
    """
    Enterprise Skill Matcher.
    """

    @staticmethod
    def match(
        candidate: Candidate,
        job: JobDescription
    ) -> MatchResult:

        result = MatchResult()

        # ------------------------------------------
        # Candidate Information
        # ------------------------------------------

        result.candidate_name = candidate.full_name

        result.email = candidate.email

        result.phone = candidate.phone

        result.source_file = candidate.source_file

        result.job_title = job.job_title

        # ------------------------------------------
        # Normalize Skills
        # ------------------------------------------

        candidate_skills = {

            skill.strip().lower()

            for skill in candidate.technical_skills

            if skill.strip()
        }

        mandatory_skills = {

            skill.strip().lower()

            for skill in job.mandatory_skills

            if skill.strip()
        }

        # ------------------------------------------
        # Matched Skills
        # ------------------------------------------

        result.matched_skills = sorted(

            list(

                mandatory_skills.intersection(
                    candidate_skills
                )

            )

        )

        # ------------------------------------------
        # Missing Skills
        # ------------------------------------------

        result.missing_skills = sorted(

            list(

                mandatory_skills.difference(
                    candidate_skills
                )

            )

        )

        # ------------------------------------------
        # Additional Skills
        # ------------------------------------------

        result.additional_skills = sorted(

            list(

                candidate_skills.difference(
                    mandatory_skills
                )

            )

        )

        # ------------------------------------------
        # Skill Score
        # ------------------------------------------

        total_required = len(
            mandatory_skills
        )

        if total_required == 0:

            result.skill_score = 100.0

        else:

            result.skill_score = round(

                (
                    len(result.matched_skills)
                    / total_required
                )
                * 100,

                2

            )

        # ------------------------------------------
        # AI Remarks
        # ------------------------------------------

        result.add_remark(

            f"Matched {len(result.matched_skills)} of "
            f"{total_required} mandatory skills."

        )

        if result.additional_skills:

            result.add_remark(

                f"Candidate has "
                f"{len(result.additional_skills)} "
                f"additional skills."

            )

        if result.missing_skills:

            result.add_remark(

                f"{len(result.missing_skills)} "
                f"mandatory skills are missing."

            )

        return result