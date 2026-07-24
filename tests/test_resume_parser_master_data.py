"""
============================================================
RecruitOS

Module      : Resume Parser Master Data Integration Test
Sprint      : 5.6.0
Version     : 1.0.0
Author      : Tamilvanan A

Purpose:
Validates integration between ResumeParser and:

    SkillExtractor
    EducationExtractor
    CertificationExtractor

============================================================
"""

from parser.resume_parser import (
    ResumeParser
)

from parser.extractors.education_extractor import (
    EducationExtractor
)

from parser.extractors.certification_extractor import (
    CertificationExtractor
)


class FakeEducationRepository:

    def get_all_degrees(self):

        return [
            "Configured Test Degree"
        ]

    def get_aliases(
        self,
        degree
    ):

        return [
            "CTD"
        ]

    def normalize_degree(
        self,
        value
    ):

        if (
            str(value)
            .strip()
            .lower()
            in {
                "configured test degree",
                "ctd"
            }
        ):

            return (
                "Configured Test Degree"
            )

        return None


class FakeCertificationRepository:

    def get_all_certifications(self):

        return [
            "Configured Test Certification"
        ]

    def get_aliases(
        self,
        certification
    ):

        return [
            "CTC"
        ]

    def normalize_certification(
        self,
        value
    ):

        if (
            str(value)
            .strip()
            .lower()
            in {
                "configured test certification",
                "ctc"
            }
        ):

            return (
                "Configured Test Certification"
            )

        return None


def main():

    print()

    print("=" * 60)

    print(
        "RecruitOS Resume Parser Master Data Integration Test"
    )

    print("=" * 60)

    original_education_repository = (
        EducationExtractor.repository
    )

    original_certification_repository = (
        CertificationExtractor.repository
    )

    try:

        EducationExtractor.repository = (
            FakeEducationRepository()
        )

        CertificationExtractor.repository = (
            FakeCertificationRepository()
        )

        document = {

            "file_name":
                "test_resume.pdf",

            "text":
                """
                Test Candidate
                test.candidate@example.com

                Total Experience:
                6 years

                Education:
                CTD

                Certifications:
                CTC
                """

        }

        candidate = (
            ResumeParser.parse(
                document
            )
        )

        print()

        print(
            "Source File     :",
            candidate.source_file
        )

        print(
            "Experience      :",
            candidate.total_experience
        )

        print(
            "Education       :",
            candidate.education
        )

        print(
            "Certifications  :",
            candidate.certifications
        )

        # ====================================================
        # Assertions
        # ====================================================

        assert (
            candidate.source_file
            == "test_resume.pdf"
        )

        assert (
            candidate.total_experience
            == 6.0
        )

        assert (
            candidate.education
            == [
                "Configured Test Degree"
            ]
        )

        assert (
            candidate.certifications
            == [
                "Configured Test Certification"
            ]
        )

        assert (
            candidate.raw_text
        )

        print()

        print(
            "ALL RESUME PARSER MASTER DATA "
            "INTEGRATION TESTS PASSED"
        )

    finally:

        EducationExtractor.repository = (
            original_education_repository
        )

        CertificationExtractor.repository = (
            original_certification_repository
        )


if __name__ == "__main__":

    main()