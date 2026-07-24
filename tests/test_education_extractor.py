"""
============================================================
RecruitOS

Module      : Education Extractor Test
Sprint      : 5.6.0
Version     : 1.0.0
Author      : Tamilvanan A

============================================================
"""

from parser.extractors.education_extractor import (
    EducationExtractor
)


class FakeEducationRepository:
    """
    Test-only repository.

    Business values here exist only inside the unit test and
    are not application master data.
    """

    def get_all_degrees(self):

        return [

            "Test Bachelor Degree",

            "Test Master Degree"

        ]

    def get_aliases(
        self,
        degree
    ):

        mapping = {

            "Test Bachelor Degree":
                [
                    "TBD",
                    "T.B.D."
                ],

            "Test Master Degree":
                [
                    "TMD"
                ]

        }

        return mapping.get(
            degree,
            []
        )

    def normalize_degree(
        self,
        value
    ):

        mapping = {

            "test bachelor degree":
                "Test Bachelor Degree",

            "tbd":
                "Test Bachelor Degree",

            "t.b.d.":
                "Test Bachelor Degree",

            "test master degree":
                "Test Master Degree",

            "tmd":
                "Test Master Degree"

        }

        return mapping.get(
            str(value).strip().lower()
        )


def main():

    print()

    print("=" * 60)

    print(
        "RecruitOS Education Extractor Test"
    )

    print("=" * 60)

    original_repository = (
        EducationExtractor.repository
    )

    try:

        EducationExtractor.repository = (
            FakeEducationRepository()
        )

        # ====================================================
        # Standard Name Test
        # ====================================================

        text = """
        Candidate completed Test Bachelor Degree
        and has relevant industry experience.
        """

        result = (
            EducationExtractor.extract(
                text
            )
        )

        print()

        print(
            "Standard Name Result :",
            result
        )

        assert result == [

            "Test Bachelor Degree"

        ]

        # ====================================================
        # Alias Test
        # ====================================================

        text = """
        EDUCATION
        TMD
        """

        result = (
            EducationExtractor.extract(
                text
            )
        )

        print(
            "Alias Result         :",
            result
        )

        assert result == [

            "Test Master Degree"

        ]

        # ====================================================
        # Multiple Qualifications
        # ====================================================

        text = """
        Qualifications:
        TBD
        Test Master Degree
        """

        result = (
            EducationExtractor.extract(
                text
            )
        )

        print(
            "Multiple Result      :",
            result
        )

        assert set(
            result
        ) == {

            "Test Bachelor Degree",

            "Test Master Degree"

        }

        # ====================================================
        # Duplicate Test
        # ====================================================

        text = """
        Test Bachelor Degree
        TBD
        T.B.D.
        """

        result = (
            EducationExtractor.extract(
                text
            )
        )

        print(
            "Duplicate Result     :",
            result
        )

        assert result == [

            "Test Bachelor Degree"

        ]

        # ====================================================
        # False Positive Boundary Test
        # ====================================================

        text = """
        The candidate is a member of the team.
        """

        result = (
            EducationExtractor.extract(
                text
            )
        )

        print(
            "Boundary Result      :",
            result
        )

        assert result == []

        # ====================================================
        # Empty Text
        # ====================================================

        assert (
            EducationExtractor.extract("")
            == []
        )

        assert (
            EducationExtractor.extract(None)
            == []
        )

        print()

        print(
            "ALL EDUCATION EXTRACTOR TESTS PASSED"
        )

    finally:

        EducationExtractor.repository = (
            original_repository
        )


if __name__ == "__main__":

    main()