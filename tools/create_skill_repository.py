"""Deprecated legacy command.

RecruitOS now uses Master_Data/RecruitOS_Configuration.xlsx as the single
configuration/master-data workbook.
"""


def main() -> None:
    raise SystemExit(
        "create_skill_repository is deprecated. Use:\n"
        "  python -m tools.create_configuration_workbook\n"
        "and manage skills in the Skills sheet of RecruitOS_Configuration.xlsx."
    )


if __name__ == "__main__":
    main()
