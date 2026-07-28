"""Claim pre-multi-user RecruitOS data for one registered private account."""
from __future__ import annotations

import argparse
from pathlib import Path

from services.legacy_data_service import LegacyDataService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Assign records migrated to the disabled legacy owner to one explicit "
            "registered RecruitOS User ID."
        )
    )
    parser.add_argument(
        "--user-id",
        required=True,
        help="Registered RecruitOS employee User ID",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=None,
        help="Optional SQLite path; defaults to database/recruitos.db",
    )
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    counts = LegacyDataService.claim_for_user(
        arguments.user_id,
        arguments.database,
    )
    print("Legacy RecruitOS data claim completed")
    for key, value in counts.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
