"""
============================================================
RecruitOS

Module      : Enterprise Skill Repository Test
Sprint      : 5.5.2
Version     : 3.0.0
Author      : Tamilvanan A

Purpose:
Validates SkillRepository integration with:

    MasterRepository
    BaseRepository
    RecruitOS_Configuration.xlsx

============================================================
"""

from services.skill_repository import (
    SkillRepository
)


def separator(
    title: str = ""
) -> None:

    print()

    print("=" * 60)

    if title:

        print(title)

        print("=" * 60)


def main():

    separator(
        "RecruitOS Enterprise Skill Repository Test"
    )

    # ====================================================
    # Initialize
    # ====================================================

    repository = SkillRepository()

    print()

    print(
        "Repository initialized successfully."
    )

    # ====================================================
    # Total Skills
    # ====================================================

    separator(
        "Repository Statistics"
    )

    total = repository.total_skills()

    print(
        f"Total Skills : {total}"
    )

    assert total >= 0

    # ====================================================
    # All Skills
    # ====================================================

    separator(
        "All Skills"
    )

    skills = repository.get_all_skills()

    for skill in skills:

        print(skill)

    assert (
        len(skills)
        == repository.total_skills()
    )

    # ====================================================
    # Categories
    # ====================================================

    separator(
        "Skill Categories"
    )

    categories = (
        repository.get_skill_categories()
    )

    for category in categories:

        print(category)

    # ====================================================
    # Validate First Skill
    # ====================================================

    if skills:

        first_skill = skills[0]

        separator(
            "Standard Skill Validation"
        )

        print(
            "Skill :",
            first_skill
        )

        print(
            "Valid :",
            repository.is_valid_skill(
                first_skill
            )
        )

        assert (
            repository.is_valid_skill(
                first_skill
            )
            is True
        )

        # ================================================
        # Details
        # ================================================

        separator(
            "Skill Details"
        )

        details = (
            repository.get_skill_details(
                first_skill
            )
        )

        print(details)

        assert details is not None

        assert (
            details["name"]
            == first_skill
        )

        # ================================================
        # Synonyms
        # ================================================

        separator(
            "Skill Synonyms"
        )

        synonyms = (
            repository.get_skill_synonyms(
                first_skill
            )
        )

        print(synonyms)

        # ================================================
        # Synonym Normalization
        # ================================================

        if synonyms:

            synonym = synonyms[0]

            separator(
                "Synonym Normalization"
            )

            print(
                "Input :",
                synonym
            )

            normalized = (
                repository.normalize_skill(
                    synonym
                )
            )

            print(
                "Standard :",
                normalized
            )

            assert (
                normalized
                == first_skill
            )

    # ====================================================
    # Invalid Skill
    # ====================================================

    separator(
        "Invalid Skill Test"
    )

    invalid_skill = (
        "__RECRUITOS_INVALID_SKILL__"
    )

    print(
        "Valid :",
        repository.is_valid_skill(
            invalid_skill
        )
    )

    assert (
        repository.is_valid_skill(
            invalid_skill
        )
        is False
    )

    assert (
        repository.normalize_skill(
            invalid_skill
        )
        is None
    )

    # ====================================================
    # Search
    # ====================================================

    if skills:

        separator(
            "Search Test"
        )

        query = skills[0]

        results = (
            repository.search_skills(
                query
            )
        )

        print(
            "Query :",
            query
        )

        print(
            "Results :",
            results
        )

        assert len(results) >= 1

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
        len(dataframe)
        == repository.total_skills()
    )

    # ====================================================
    # Summary
    # ====================================================

    repository.display_summary()

    separator(
        "ALL SKILL REPOSITORY TESTS PASSED"
    )


if __name__ == "__main__":

    main()