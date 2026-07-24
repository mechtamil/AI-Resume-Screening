"""
============================================================
RecruitOS

Module      : Enterprise Certification Repository Test
Sprint      : 5.5.4
Version     : 2.0.0
Author      : Tamilvanan A

Purpose:
Validates CertificationRepository integration with:

    - MasterRepository
    - BaseRepository
    - RecruitOS_Configuration.xlsx

This test is data-driven.

It does not depend on any hardcoded real-world
certification names.

============================================================
"""

from services.certification_repository import (
    CertificationRepository
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
        "RecruitOS Enterprise Certification Repository Test"
    )

    # ====================================================
    # Initialize Repository
    # ====================================================

    repository = (
        CertificationRepository()
    )

    print()

    print(
        "Repository initialized successfully."
    )

    # ====================================================
    # Statistics
    # ====================================================

    separator(
        "Repository Statistics"
    )

    total = (
        repository.total_certifications()
    )

    print(
        "Total Certifications :",
        total
    )

    assert total >= 0

    # ====================================================
    # All Certifications
    # ====================================================

    separator(
        "Configured Certifications"
    )

    certifications = (
        repository.get_all_certifications()
    )

    for certification in certifications:

        print(
            certification
        )

    assert (
        len(certifications)
        == total
    )

    # ====================================================
    # Compatibility APIs
    # ====================================================

    separator(
        "Compatibility API Test"
    )

    assert (
        repository.get_all()
        == certifications
    )

    assert (
        repository.get_certification_names()
        == certifications
    )

    print(
        "get_all()                  : PASS"
    )

    print(
        "get_certification_names()  : PASS"
    )

    # ====================================================
    # First Configured Certification
    # ====================================================

    if certifications:

        first_certification = (
            certifications[0]
        )

        # ================================================
        # Standard Validation
        # ================================================

        separator(
            "Standard Certification Validation"
        )

        print(
            "Certification :",
            first_certification
        )

        valid = (
            repository.is_valid_certification(
                first_certification
            )
        )

        print(
            "Valid :",
            valid
        )

        assert valid is True

        assert (
            repository.is_valid(
                first_certification
            )
            is True
        )

        # ================================================
        # Standard Normalization
        # ================================================

        separator(
            "Standard Certification Normalization"
        )

        normalized = (
            repository.normalize_certification(
                first_certification
            )
        )

        print(
            "Input    :",
            first_certification
        )

        print(
            "Standard :",
            normalized
        )

        assert (
            normalized
            == first_certification
        )

        assert (
            repository.get_standard_name(
                first_certification
            )
            == first_certification
        )

        # ================================================
        # Certification Details
        # ================================================

        separator(
            "Certification Details"
        )

        details = (
            repository.get_certification_details(
                first_certification
            )
        )

        print(
            details
        )

        assert details is not None

        assert (
            details["name"]
            == first_certification
        )

        # ================================================
        # Category
        # ================================================

        separator(
            "Certification Category"
        )

        category = (
            repository.get_category(
                first_certification
            )
        )

        print(
            "Certification :",
            first_certification
        )

        print(
            "Category      :",
            category
        )

        # Category is optional.
        # No hardcoded expected category is used.

        # ================================================
        # Aliases
        # ================================================

        separator(
            "Certification Aliases"
        )

        aliases = (
            repository.get_aliases(
                first_certification
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

            alias_standard = (
                repository.normalize_certification(
                    first_alias
                )
            )

            print(
                "Standard :",
                alias_standard
            )

            assert (
                alias_standard
                == first_certification
            )

            assert (
                repository.find_alias(
                    first_alias
                )
                == first_certification
            )

            assert (
                repository.is_valid_certification(
                    first_alias
                )
                is True
            )

        # ================================================
        # Search
        # ================================================

        separator(
            "Certification Search"
        )

        results = (
            repository.search_certifications(
                first_certification
            )
        )

        print(
            "Query :",
            first_certification
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
    # Categories
    # ====================================================

    separator(
        "Certification Categories"
    )

    categories = (
        repository.get_categories()
    )

    for category in categories:

        print(
            category
        )

    if categories:

        first_category = (
            categories[0]
        )

        category_certifications = (
            repository.get_certifications_by_category(
                first_category
            )
        )

        print()

        print(
            "First Category :",
            first_category
        )

        print(
            "Certifications :",
            category_certifications
        )

        assert (
            len(category_certifications)
            >= 1
        )

    # ====================================================
    # Invalid Certification
    # ====================================================

    separator(
        "Invalid Certification Test"
    )

    invalid_value = (
        "__RECRUITOS_INVALID_CERTIFICATION__"
    )

    assert (
        repository.is_valid_certification(
            invalid_value
        )
        is False
    )

    assert (
        repository.is_valid(
            invalid_value
        )
        is False
    )

    assert (
        repository.normalize_certification(
            invalid_value
        )
        is None
    )

    assert (
        repository.get_standard_name(
            invalid_value
        )
        is None
    )

    assert (
        repository.get_certification_details(
            invalid_value
        )
        is None
    )

    assert (
        repository.get_aliases(
            invalid_value
        )
        == []
    )

    print(
        "Invalid certification handling : PASS"
    )

    # ====================================================
    # Alias Parser Test
    # ====================================================

    separator(
        "Alias Parser Test"
    )

    parsed_aliases = (
        CertificationRepository._parse_aliases(
            "Alias One;Alias Two,Alias Three|Alias Four"
        )
    )

    expected_aliases = [

        "Alias One",

        "Alias Two",

        "Alias Three",

        "Alias Four"

    ]

    print(
        "Parsed :",
        parsed_aliases
    )

    assert (
        parsed_aliases
        == expected_aliases
    )

    print(
        "Multiple delimiter handling : PASS"
    )

    # ====================================================
    # DataFrame
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
        "Certification"
        in dataframe.columns
    )

    assert (
        repository.total_certifications()
        <= len(dataframe)
    )

    # ====================================================
    # Repository Summary
    # ====================================================

    repository.display_summary()

    # ====================================================
    # Final Result
    # ====================================================

    separator(
        "ALL CERTIFICATION REPOSITORY TESTS PASSED"
    )


if __name__ == "__main__":

    main()