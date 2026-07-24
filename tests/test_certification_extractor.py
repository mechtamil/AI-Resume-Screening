"""
============================================================
RecruitOS

Module      : Certification Extractor Test
Sprint      : 5.6.0
Version     : 2.0.0
Author      : Tamilvanan A

============================================================
"""

from parser.extractors.certification_extractor import (
    CertificationExtractor
)


class FakeCertificationRepository:
    """
    Test-only certification repository.
    """

    def get_all_certifications(self):

        return [

            "Test Professional Certification",

            "Test Advanced Certification"

        ]

    def get_aliases(
        self,
        certification
    ):

        mapping = {

            "Test Professional Certification":
                [
                    "TPC"
                ],

            "Test Advanced Certification":
                [
                    "TAC",
                    "T.A.C."
                ]

        }

        return mapping.get(
            certification,
            []
        )

    def normalize_certification(
        self,
        value
    ):

        mapping = {

            "test professional certification":
                "Test Professional Certification",

            "tpc":
                "Test Professional Certification",

            "test advanced certification":
                "Test Advanced Certification",

            "tac":
                "Test Advanced Certification",

            "t.a.c.":
                "Test Advanced Certification"

        }

        return mapping.get(
            str(value).strip().lower()
        )


def main():

    print()

    print("=" * 60)

    print(
        "RecruitOS Certification Extractor Test"
    )

    print("=" * 60)

    original_repository = (
        CertificationExtractor.repository
    )

    try:

        CertificationExtractor.repository = (
            FakeCertificationRepository()
        )

        # ====================================================
        # Standard Certification
        # ====================================================

        text = """
        Certifications:
        Test Professional Certification
        """

        result = (
            CertificationExtractor.extract(
                text
            )
        )

        print()

        print(
            "Standard Result :",
            result
        )

        assert result == [

            "Test Professional Certification"

        ]

        # ====================================================
        # Alias
        # ====================================================

        text = """
        Professional Credentials
        TAC
        """

        result = (
            CertificationExtractor.extract(
                text
            )
        )

        print(
            "Alias Result    :",
            result
        )

        assert result == [

            "Test Advanced Certification"

        ]

        # ====================================================
        # Multiple
        # ====================================================

        text = """
        TPC
        Test Advanced Certification
        """

        result = (
            CertificationExtractor.extract(
                text
            )
        )

        print(
            "Multiple Result :",
            result
        )

        assert set(
            result
        ) == {

            "Test Professional Certification",

            "Test Advanced Certification"

        }

        # ====================================================
        # Duplicate
        # ====================================================

        text = """
        Test Advanced Certification
        TAC
        T.A.C.
        """

        result = (
            CertificationExtractor.extract(
                text
            )
        )

        print(
            "Duplicate Result:",
            result
        )

        assert result == [

            "Test Advanced Certification"

        ]

        # ====================================================
        # Empty
        # ====================================================

        assert (
            CertificationExtractor.extract("")
            == []
        )

        assert (
            CertificationExtractor.extract(None)
            == []
        )

        print()

        print(
            "ALL CERTIFICATION EXTRACTOR TESTS PASSED"
        )

    finally:

        CertificationExtractor.repository = (
            original_repository
        )


if __name__ == "__main__":

    main()