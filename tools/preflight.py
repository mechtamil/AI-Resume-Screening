"""RecruitOS preflight validation for developer setup and deployment checks."""
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from config.settings import APP_NAME, VERSION
from services.configuration_validator import ConfigurationValidator


def main() -> int:
    print(f"{APP_NAME} {VERSION} preflight")
    report = ConfigurationValidator.validate()
    if report["warnings"]:
        print("Warnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")
    if report["errors"]:
        print("Errors:")
        for error in report["errors"]:
            print(f"  - {error}")
        return 1
    print("Configuration: OK")
    print("Core imports: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
