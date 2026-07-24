"""
============================================================
RecruitOS

Module      : Enterprise Scoring Repository Test
Sprint      : 5.5.5
Version     : 1.0.0
Author      : Tamilvanan A

Purpose:
Validates ScoringRepository integration with:

    - MasterRepository
    - BaseRepository
    - RecruitOS_Configuration.xlsx

The test is data-driven.

It does not depend on hardcoded scoring component names
or scoring weights.

============================================================
"""

from services.scoring_repository import (
    ScoringRepository
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

        print(
            title
        )

        print("=" * 60)


def main() -> None:

    separator(
        "RecruitOS Enterprise Scoring Repository Test"
    )

    # ====================================================
    # Initialize Repository
    # ====================================================

    repository = (
        ScoringRepository()
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

    total_components = (
        repository.total_components()
    )

    total_weight = (
        repository.get_total_weight()
    )

    print(
        "Active Components :",
        total_components
    )

    print(
        "Total Weight      :",
        total_weight
    )

    assert (
        total_components
        >= 0
    )

    assert (
        total_weight
        >= 0
    )

    # ====================================================
    # Active Components
    # ====================================================

    separator(
        "Active Components"
    )

    components = (
        repository.get_active_components()
    )

    for component in components:

        print(
            component
        )

    assert (
        len(components)
        == total_components
    )

    assert (
        repository.get_components()
        == components
    )

    # ====================================================
    # All Weights
    # ====================================================

    separator(
        "Configured Weights"
    )

    weights = (
        repository.get_all_weights()
    )

    print(
        weights
    )

    assert (
        len(weights)
        == total_components
    )

    calculated_total = sum(
        weights.values()
    )

    assert (
        abs(
            calculated_total
            - total_weight
        )
        < 0.000001
    )

    # ====================================================
    # First Configured Component
    # ====================================================

    if components:

        first_component = (
            components[0]
        )

        separator(
            "Component Validation"
        )

        print(
            "Component :",
            first_component
        )

        valid = (
            repository.is_valid_component(
                first_component
            )
        )

        print(
            "Valid :",
            valid
        )

        assert (
            valid
            is True
        )

        # ================================================
        # Weight
        # ================================================

        separator(
            "Component Weight"
        )

        weight = (
            repository.get_weight(
                first_component
            )
        )

        print(
            "Component :",
            first_component
        )

        print(
            "Weight    :",
            weight
        )

        assert (
            weight
            is not None
        )

        assert (
            weight
            >= 0
        )

        # ================================================
        # Required Weight
        # ================================================

        required_weight = (
            repository.require_weight(
                first_component
            )
        )

        assert (
            required_weight
            == weight
        )

        # ================================================
        # Component Details
        # ================================================

        separator(
            "Component Details"
        )

        details = (
            repository.get_component_details(
                first_component
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
            details["name"]
            == first_component
        )

        assert (
            details["weight"]
            == weight
        )

        # ================================================
        # Remarks
        # ================================================

        separator(
            "Component Remarks"
        )

        remarks = (
            repository.get_remarks(
                first_component
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
            "Component Search"
        )

        results = (
            repository.search_components(
                first_component
            )
        )

        print(
            "Query :",
            first_component
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
    # Invalid Component
    # ====================================================

    separator(
        "Invalid Component Test"
    )

    invalid_component = (
        "__RECRUITOS_INVALID_SCORING_COMPONENT__"
    )

    assert (
        repository.is_valid_component(
            invalid_component
        )
        is False
    )

    assert (
        repository.get_weight(
            invalid_component
        )
        is None
    )

    assert (
        repository.get_component_details(
            invalid_component
        )
        is None
    )

    assert (
        repository.get_remarks(
            invalid_component
        )
        is None
    )

    print(
        "Invalid component handling : PASS"
    )

    # ====================================================
    # require_weight Error Test
    # ====================================================

    separator(
        "Required Weight Error Test"
    )

    try:

        repository.require_weight(
            invalid_component
        )

        raise AssertionError(
            "Expected KeyError was not raised."
        )

    except KeyError:

        print(
            "Missing required component correctly "
            "raises KeyError : PASS"
        )

    # ====================================================
    # Total Weight Validation
    # ====================================================

    separator(
        "Total Weight Validation"
    )

    # The expected value is intentionally supplied by the
    # caller instead of being hardcoded in the repository.

    validation_result = (
        repository.validate_total_weight(
            total_weight
        )
    )

    print(
        "Configured Total :",
        total_weight
    )

    print(
        "Validation       :",
        validation_result
    )

    assert (
        validation_result
        is True
    )

    # ====================================================
    # All Component Details
    # ====================================================

    separator(
        "All Component Details"
    )

    all_details = (
        repository.get_all_component_details()
    )

    for item in all_details:

        print(
            item
        )

    assert (
        len(all_details)
        == total_components
    )

    # ====================================================
    # Weight Parser Tests
    # ====================================================

    separator(
        "Weight Parser Test"
    )

    assert (
        ScoringRepository._parse_weight(
            10,
            "Test Component"
        )
        == 10.0
    )

    assert (
        ScoringRepository._parse_weight(
            "25.5",
            "Test Component"
        )
        == 25.5
    )

    print(
        "Numeric conversion : PASS"
    )

    try:

        ScoringRepository._parse_weight(
            "invalid",
            "Test Component"
        )

        raise AssertionError(
            "Expected ValueError was not raised."
        )

    except ValueError:

        print(
            "Invalid numeric value detection : PASS"
        )

    try:

        ScoringRepository._parse_weight(
            -1,
            "Test Component"
        )

        raise AssertionError(
            "Expected ValueError was not raised."
        )

    except ValueError:

        print(
            "Negative weight detection : PASS"
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
        "Component"
        in dataframe.columns
    )

    assert (
        "Weight"
        in dataframe.columns
    )

    # ====================================================
    # Summary
    # ====================================================

    repository.display_summary()

    # ====================================================
    # Final Result
    # ====================================================

    separator(
        "ALL SCORING REPOSITORY TESTS PASSED"
    )


if __name__ == "__main__":

    main()