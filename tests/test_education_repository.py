"""
============================================================
RecruitOS

Module      : Enterprise Education Repository Test
Sprint      : 5.5.3
Version     : 1.0.0
Author      : Tamilvanan A

Purpose:
Tests EducationRepository integration with:

    - MasterRepository
    - BaseRepository
    - RecruitOS_Configuration.xlsx

The test is data-driven.

It does not depend on hardcoded degree names.

============================================================
"""

from services.education_repository import (
    EducationRepository
)


def separator(
    title: str = ""
) -> None:
    """
    Print test section separator.
    """

    print()

    print("=" * 60)

    if title:

        print(title)

        print("=" * 60)


def main() -> None:

    separator(
        "RecruitOS Enterprise Education Repository Test"
    )

    # ====================================================
    # Repository Initialization
    # ====================================================

    repository = (
        EducationRepository()
    )

    print()

    print(
        "Repository initialized successfully."
    )

    # ====================================================
    # Repository Statistics
    # ====================================================

    separator(
        "Repository Statistics"
    )

    total = (
        repository.total_degrees()
    )

    print(
        f"Total Degrees : {total}"
    )

    assert total >= 0

    # ====================================================
    # All Degrees
    # ====================================================

    separator(
        "Configured Education"
    )

    degrees = (
        repository.get_all_degrees()
    )

    for degree in degrees:

        print(degree)

    assert (
        len(degrees)
        == repository.total_degrees()
    )

    # ====================================================
    # Test First Available Record
    # ====================================================

    if degrees:

        first_degree = (
            degrees[0]
        )

        # ================================================
        # Validation
        # ================================================

        separator(
            "Standard Degree Validation"
        )

        print(
            "Degree :",
            first_degree
        )

        valid = (
            repository.is_valid_degree(
                first_degree
            )
        )

        print(
            "Valid :",
            valid
        )

        assert valid is True

        # ================================================
        # Normalization
        # ================================================

        separator(
            "Standard Degree Normalization"
        )

        normalized = (
            repository.normalize_degree(
                first_degree
            )
        )

        print(
            "Input    :",
            first_degree
        )

        print(
            "Standard :",
            normalized
        )

        assert (
            normalized
            == first_degree
        )

        # ================================================
        # Degree Details
        # ================================================

        separator(
            "Degree Details"
        )

        details = (
            repository.get_degree_details(
                first_degree
            )
        )

        print(
            details
        )

        assert details is not None

        assert (
            details["name"]
            == first_degree
        )

        # ================================================
        # Aliases
        # ================================================

        separator(
            "Education Aliases"
        )

        aliases = (
            repository.get_aliases(
                first_degree
            )
        )

        print(
            aliases
        )

        # ================================================
        # Alias Normalization
        # ================================================

        if aliases:

            first_alias = (
                aliases[0]
            )

            separator(
                "Alias Normalization"
            )

            print(
                "Alias :",
                first_alias
            )

            normalized_alias = (
                repository.normalize_degree(
                    first_alias
                )
            )

            print(
                "Standard :",
                normalized_alias
            )

            assert (
                normalized_alias
                == first_degree
            )

            assert (
                repository.is_valid_degree(
                    first_alias
                )
                is True
            )

        # ================================================
        # Priority
        # ================================================

        separator(
            "Education Priority"
        )

        priority = (
            repository.get_priority(
                first_degree
            )
        )

        print(
            "Degree   :",
            first_degree
        )

        print(
            "Priority :",
            priority
        )

        # Priority may intentionally be blank.
        # Therefore no hardcoded expected value is used.

        # ================================================
        # Search
        # ================================================

        separator(
            "Education Search"
        )

        results = (
            repository.search_degrees(
                first_degree
            )
        )

        print(
            "Query :",
            first_degree
        )

        print(
            "Results :",
            results
        )

        assert (
            len(results)
            >= 1
        )

    # ====================================================
    # Invalid Degree
    # ====================================================

    separator(
        "Invalid Degree Test"
    )

    invalid_degree = (
        "__RECRUITOS_INVALID_EDUCATION__"
    )

    valid = (
        repository.is_valid_degree(
            invalid_degree
        )
    )

    print(
        "Valid :",
        valid
    )

    assert valid is False

    assert (
        repository.normalize_degree(
            invalid_degree
        )
        is None
    )

    assert (
        repository.get_degree_details(
            invalid_degree
        )
        is None
    )

    assert (
        repository.get_aliases(
            invalid_degree
        )
        == []
    )

    # ====================================================
    # DataFrame Test
    # ====================================================

    separator(
        "DataFrame Test"
    )

    dataframe = (
        repository.get_dataframe()
    )

    print(
        "Rows :",
        len(dataframe)
    )

    print(
        "Columns :",
        list(
            dataframe.columns
        )
    )

    assert (
        len(dataframe)
        == repository.total_degrees()
    )

    # ====================================================
    # Repository Summary
    # ====================================================

    repository.display_summary()

    # ====================================================
    # Final Result
    # ====================================================

    separator(
        "ALL EDUCATION REPOSITORY TESTS PASSED"
    )


if __name__ == "__main__":

    main()