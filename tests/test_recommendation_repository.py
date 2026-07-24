"""
============================================================
RecruitOS

Module      : Enterprise Recommendation Repository Test
Sprint      : 5.5.6
Version     : 1.0.0
Author      : Tamilvanan A

Purpose:
Validates RecommendationRepository integration with:

    - MasterRepository
    - BaseRepository
    - RecruitOS_Configuration.xlsx

Tests are data-driven and do not depend on hardcoded
recommendation labels or thresholds.

============================================================
"""

from services.recommendation_repository import (
    RecommendationRepository
)


def separator(
    title: str = ""
) -> None:

    print()

    print("=" * 60)

    if title:

        print(
            title
        )

        print("=" * 60)


def main() -> None:

    separator(
        "RecruitOS Enterprise Recommendation Repository Test"
    )

    # ====================================================
    # Initialize
    # ====================================================

    repository = (
        RecommendationRepository()
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
        repository.total_recommendations()
    )

    print(
        "Recommendation Rules :",
        total
    )

    assert total >= 0

    # ====================================================
    # All Recommendations
    # ====================================================

    separator(
        "Configured Recommendation Rules"
    )

    rules = (
        repository.get_all_recommendations()
    )

    for rule in rules:

        print(
            rule
        )

    assert (
        len(rules)
        == total
    )

    # ====================================================
    # Names
    # ====================================================

    names = (
        repository.get_recommendation_names()
    )

    assert (
        len(names)
        == total
    )

    # ====================================================
    # Test Every Configured Range
    # ====================================================

    separator(
        "Recommendation Resolution Tests"
    )

    for rule in rules:

        recommendation = (
            rule[
                "recommendation"
            ]
        )

        minimum = (
            rule[
                "minimum_score"
            ]
        )

        maximum = (
            rule[
                "maximum_score"
            ]
        )

        midpoint = (
            minimum
            + maximum
        ) / 2

        print()

        print(
            "Recommendation :",
            recommendation
        )

        print(
            "Range          :",
            minimum,
            "-",
            maximum
        )

        print(
            "Test Score     :",
            midpoint
        )

        result = (
            repository.get_recommendation(
                midpoint
            )
        )

        print(
            "Result         :",
            result
        )

        assert (
            result
            == recommendation
        )

        # Minimum boundary must match.

        assert (
            repository.get_recommendation(
                minimum
            )
            == recommendation
        )

        # Maximum boundary must match.

        assert (
            repository.get_recommendation(
                maximum
            )
            == recommendation
        )

    # ====================================================
    # First Recommendation Details
    # ====================================================

    if names:

        first_name = (
            names[0]
        )

        separator(
            "Recommendation Details"
        )

        details = (
            repository.get_recommendation_details(
                first_name
            )
        )

        print(
            details
        )

        assert (
            details
            is not None
        )

        assert (
            details[
                "recommendation"
            ]
            == first_name
        )

        # ================================================
        # Validation
        # ================================================

        assert (
            repository.is_valid_recommendation(
                first_name
            )
            is True
        )

        # ================================================
        # Range
        # ================================================

        score_range = (
            repository.get_score_range(
                first_name
            )
        )

        print(
            "Score Range :",
            score_range
        )

        assert (
            score_range
            is not None
        )

        # ================================================
        # Remarks
        # ================================================

        remarks = (
            repository.get_remarks(
                first_name
            )
        )

        print(
            "Remarks :",
            remarks
        )

        # Remarks may intentionally be blank.

        # ================================================
        # Search
        # ================================================

        separator(
            "Recommendation Search"
        )

        results = (
            repository.search_recommendations(
                first_name
            )
        )

        print(
            "Query   :",
            first_name
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
    # Invalid Recommendation
    # ====================================================

    separator(
        "Invalid Recommendation Test"
    )

    invalid_name = (
        "__RECRUITOS_INVALID_RECOMMENDATION__"
    )

    assert (
        repository.is_valid_recommendation(
            invalid_name
        )
        is False
    )

    assert (
        repository.get_recommendation_details(
            invalid_name
        )
        is None
    )

    assert (
        repository.get_score_range(
            invalid_name
        )
        is None
    )

    assert (
        repository.get_remarks(
            invalid_name
        )
        is None
    )

    print(
        "Invalid recommendation handling : PASS"
    )

    # ====================================================
    # Score Parsing Tests
    # ====================================================

    separator(
        "Score Parsing Test"
    )

    assert (
        RecommendationRepository._parse_input_score(
            50
        )
        == 50.0
    )

    assert (
        RecommendationRepository._parse_input_score(
            "75.5"
        )
        == 75.5
    )

    print(
        "Numeric score conversion : PASS"
    )

    try:

        RecommendationRepository._parse_input_score(
            "invalid"
        )

        raise AssertionError(
            "Expected ValueError was not raised."
        )

    except ValueError:

        print(
            "Invalid score detection : PASS"
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
        "Minimum Score"
        in dataframe.columns
    )

    assert (
        "Maximum Score"
        in dataframe.columns
    )

    assert (
        "Recommendation"
        in dataframe.columns
    )

    # ====================================================
    # Summary
    # ====================================================

    repository.display_summary()

    separator(
        "ALL RECOMMENDATION REPOSITORY TESTS PASSED"
    )


if __name__ == "__main__":

    main()