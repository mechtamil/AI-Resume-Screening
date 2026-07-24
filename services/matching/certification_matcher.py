"""
============================================================
RecruitOS

Enterprise Certification Matcher

Version : 1.0
Author  : Tamilvanan A
============================================================
"""

from models.candidate import Candidate

from JD.jd_model import JobDescription

from models.match_result import MatchResult


class CertificationMatcher:

    @staticmethod
    def match(

        candidate: Candidate,

        job: JobDescription,

        result: MatchResult

    ):

        candidate_certifications = {

            c.strip().lower()

            for c in candidate.certifications

            if c.strip()

        }

        required_certifications = {

            c.strip().lower()

            for c in job.certifications

            if c.strip()

        }

        # ---------------------------------------

        if not required_certifications:

            result.certification_score = 100

            result.certification_match = True

            result.add_remark(

                "No certification requirement specified."

            )

            return result

        # ---------------------------------------

        matched = sorted(

            list(

                required_certifications.intersection(

                    candidate_certifications

                )

            )

        )

        missing = sorted(

            list(

                required_certifications.difference(

                    candidate_certifications

                )

            )

        )

        result.matched_certifications = matched

        result.missing_certifications = missing

        total = len(

            required_certifications

        )

        result.certification_score = round(

            (

                len(matched)

                / total

            ) * 100,

            2

        )

        result.certification_match = (

            len(missing) == 0

        )

        result.add_remark(

            f"Matched {len(matched)} of {total} required certifications."

        )

        if missing:

            result.add_remark(

                f"{len(missing)} certifications are missing."

            )

        return result