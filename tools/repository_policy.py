"""RecruitOS repository policy and sensitive-file guard.

The policy can inspect the current filesystem or only Git-tracked files. It is used
locally, during CI, and before creating a clean source release.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence


@dataclass(frozen=True)
class PolicyFinding:
    """One repository-policy violation or warning."""

    severity: str
    code: str
    path: str
    message: str


class RepositoryPolicy:
    """Validate RecruitOS source-control contents."""

    REQUIRED_FILES = (
        "app.py",
        "VERSION",
        "requirements.txt",
        ".gitignore",
        "Master_Data/RecruitOS_Configuration.xlsx",
    )

    EXCLUDED_SCAN_DIRECTORIES = {
        ".git",
        ".venv",
        "venv",
        "env",
        "dist",
        "build",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "htmlcov",
    }

    CACHE_PARTS = {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "htmlcov",
    }

    SECRET_NAMES = {
        ".env",
        "secrets.toml",
        "credentials.json",
        "service-account.json",
    }

    SECRET_SUFFIXES = {
        ".pem",
        ".key",
        ".p12",
        ".pfx",
    }

    DATABASE_SUFFIXES = {
        ".db",
        ".sqlite",
        ".sqlite3",
    }

    PACKAGE_ARTIFACT_NAMES = {
        "PACKAGE_MANIFEST_SHA256.txt",
        "README_APPLY.txt",
    }

    RUNTIME_ROOTS = {
        "uploads",
        "output",
        "temp",
        "logs",
        "Resume",
    }

    MAX_TRACKED_FILE_BYTES = 25 * 1024 * 1024

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def git_tracked_files(self) -> list[str]:
        """Return normalized paths tracked by Git."""
        completed = subprocess.run(
            ["git", "-C", str(self.root), "ls-files", "-z"],
            check=False,
            capture_output=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "Git-tracked inspection requires a valid Git repository."
            )
        decoded = completed.stdout.decode("utf-8", errors="surrogateescape")
        return sorted(path for path in decoded.split("\0") if path)

    def filesystem_files(self) -> list[str]:
        """Return source-tree files without following symlinked directories."""
        discovered: list[str] = []
        for candidate in self.root.rglob("*"):
            if not candidate.is_file() and not candidate.is_symlink():
                continue
            relative = candidate.relative_to(self.root)
            if any(part in self.EXCLUDED_SCAN_DIRECTORIES for part in relative.parts):
                continue
            discovered.append(relative.as_posix())
        return sorted(discovered)

    def validate(
        self,
        paths: Sequence[str] | None = None,
        *,
        require_required_files: bool = True,
    ) -> list[PolicyFinding]:
        """Validate supplied paths or the complete filesystem source tree."""
        selected = list(paths) if paths is not None else self.filesystem_files()
        findings: list[PolicyFinding] = []
        normalized = {PurePosixPath(path).as_posix() for path in selected}

        if require_required_files:
            for required in self.REQUIRED_FILES:
                if required not in normalized and not (self.root / required).is_file():
                    findings.append(
                        PolicyFinding(
                            "error",
                            "REQUIRED_FILE_MISSING",
                            required,
                            "Required RecruitOS source file is missing.",
                        )
                    )

        for raw_path in sorted(normalized):
            findings.extend(self._validate_path(raw_path))
        return findings

    def _validate_path(self, raw_path: str) -> list[PolicyFinding]:
        path = PurePosixPath(raw_path)
        parts = set(path.parts)
        name = path.name
        suffix = path.suffix.casefold()
        findings: list[PolicyFinding] = []

        if path.is_absolute() or ".." in path.parts:
            findings.append(
                PolicyFinding(
                    "error",
                    "UNSAFE_PATH",
                    raw_path,
                    "Repository entry must be relative and cannot contain '..'.",
                )
            )
            return findings

        if self.CACHE_PARTS.intersection(parts) or suffix in {".pyc", ".pyo"}:
            findings.append(
                PolicyFinding(
                    "error",
                    "PYTHON_CACHE_TRACKED",
                    raw_path,
                    "Generated Python/test cache must not be committed.",
                )
            )

        if name in self.PACKAGE_ARTIFACT_NAMES or suffix == ".zip":
            findings.append(
                PolicyFinding(
                    "error",
                    "PACKAGE_ARTIFACT_TRACKED",
                    raw_path,
                    "Local sprint/release package artifact must remain outside Git.",
                )
            )

        if name.casefold() in self.SECRET_NAMES or suffix in self.SECRET_SUFFIXES:
            allowed_example = raw_path == ".env.example"
            if not allowed_example:
                findings.append(
                    PolicyFinding(
                        "error",
                        "SECRET_FILE_TRACKED",
                        raw_path,
                        "Secret or credential file must not be committed.",
                    )
                )

        if suffix in self.DATABASE_SUFFIXES or name.endswith(".db-backup"):
            findings.append(
                PolicyFinding(
                    "error",
                    "DATABASE_TRACKED",
                    raw_path,
                    "Runtime database or database backup must not be committed.",
                )
            )

        if path.parts and path.parts[0] in self.RUNTIME_ROOTS and name != ".gitkeep":
            findings.append(
                PolicyFinding(
                    "error",
                    "RUNTIME_DATA_TRACKED",
                    raw_path,
                    "Runtime upload, output, log, temporary or resume data is prohibited.",
                )
            )

        if path.parts and path.parts[0] == "JD" and suffix in {".pdf", ".docx"}:
            findings.append(
                PolicyFinding(
                    "error",
                    "JOB_DOCUMENT_TRACKED",
                    raw_path,
                    "Uploaded or real job-description documents must not be committed.",
                )
            )

        if (
            len(path.parts) >= 2
            and path.parts[0] == "Master_Data"
            and name.casefold() != "recruitos_configuration.xlsx"
            and suffix in {".xlsx", ".xls"}
        ):
            findings.append(
                PolicyFinding(
                    "error",
                    "LEGACY_MASTER_TRACKED",
                    raw_path,
                    "Only the central RecruitOS configuration workbook is authoritative.",
                )
            )

        full_path = self.root / Path(*path.parts)
        if full_path.is_symlink():
            findings.append(
                PolicyFinding(
                    "error",
                    "SYMLINK_TRACKED",
                    raw_path,
                    "Symlinks are not permitted in clean RecruitOS source releases.",
                )
            )
        elif full_path.is_file() and full_path.stat().st_size > self.MAX_TRACKED_FILE_BYTES:
            findings.append(
                PolicyFinding(
                    "warning",
                    "LARGE_TRACKED_FILE",
                    raw_path,
                    "Tracked file exceeds 25 MB and requires explicit review.",
                )
            )

        return findings

    @staticmethod
    def errors(findings: Iterable[PolicyFinding]) -> list[PolicyFinding]:
        return [finding for finding in findings if finding.severity == "error"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate RecruitOS repository policy.")
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parent.parent),
        help="RecruitOS repository root.",
    )
    parser.add_argument(
        "--tracked",
        action="store_true",
        help="Inspect only files tracked by Git.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON.",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Return failure when warnings are present.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    policy = RepositoryPolicy(args.root)
    try:
        paths = policy.git_tracked_files() if args.tracked else None
        findings = policy.validate(paths)
    except RuntimeError as exc:
        print(f"Repository policy: ERROR\n  - {exc}")
        return 2

    if args.json:
        print(json.dumps([asdict(item) for item in findings], indent=2))
    else:
        if findings:
            print("RecruitOS repository policy findings:")
            for finding in findings:
                print(
                    f"  [{finding.severity.upper()}] {finding.code}: "
                    f"{finding.path} — {finding.message}"
                )
        else:
            print("RecruitOS repository policy: OK")

    has_errors = bool(policy.errors(findings))
    has_warnings = any(item.severity == "warning" for item in findings)
    return 1 if has_errors or (args.fail_on_warning and has_warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
