"""Build a deterministic, policy-validated RecruitOS source ZIP."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import zipfile
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence

from tools.repository_policy import RepositoryPolicy

FIXED_ZIP_TIMESTAMP = (2020, 1, 1, 0, 0, 0)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_version(root: Path) -> str:
    value = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not value:
        raise ValueError("VERSION cannot be empty.")
    return value


def git_is_clean(root: Path) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError("A valid Git repository is required for a clean release build.")
    return not completed.stdout.strip()


def build_clean_release(
    root: str | Path,
    output_path: str | Path,
    *,
    files: Iterable[str] | None = None,
    require_clean_git: bool = True,
) -> Path:
    """Create a deterministic source ZIP from policy-approved files.

    When ``files`` is omitted, only Git-tracked files are packaged. This prevents
    ignored local CVs, databases, reports and secrets from entering a release.
    """
    source_root = Path(root).resolve()
    destination = Path(output_path).resolve()
    policy = RepositoryPolicy(source_root)

    if require_clean_git and not git_is_clean(source_root):
        raise RuntimeError("Git working tree must be clean before building a source release.")

    selected = sorted(set(files if files is not None else policy.git_tracked_files()))
    findings = policy.validate(selected)
    errors = policy.errors(findings)
    if errors:
        details = "; ".join(f"{item.code}:{item.path}" for item in errors)
        raise ValueError(f"Repository policy failed: {details}")

    version = read_version(source_root)
    package_root = f"RecruitOS-v{version}"
    destination.parent.mkdir(parents=True, exist_ok=True)

    manifest_lines: list[str] = []
    entries: list[tuple[str, bytes]] = []
    for relative_text in selected:
        relative = PurePosixPath(relative_text)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Unsafe release path: {relative_text}")
        full_path = source_root / Path(*relative.parts)
        if not full_path.is_file() or full_path.is_symlink():
            raise ValueError(f"Release source is missing or unsafe: {relative_text}")
        payload = full_path.read_bytes()
        digest = sha256_bytes(payload)
        manifest_lines.append(f"{digest}  {relative.as_posix()}")
        entries.append((f"{package_root}/{relative.as_posix()}", payload))

    manifest_payload = ("\n".join(manifest_lines) + "\n").encode("utf-8")
    entries.append((f"{package_root}/SOURCE_MANIFEST_SHA256.txt", manifest_payload))

    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for archive_name, payload in sorted(entries):
            info = zipfile.ZipInfo(archive_name, date_time=FIXED_ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, payload)

    return destination


def _build_parser() -> argparse.ArgumentParser:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Build clean RecruitOS source ZIP.")
    parser.add_argument("--root", default=str(root))
    parser.add_argument("--output", default="")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Development/testing only; normal release builds require a clean Git tree.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    version = read_version(root)
    output = (
        Path(args.output).resolve()
        if args.output
        else root / "dist" / f"RecruitOS-v{version}-source.zip"
    )
    try:
        final_path = build_clean_release(
            root,
            output,
            require_clean_git=not args.allow_dirty,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Clean source release: ERROR\n  - {exc}")
        return 1

    print(f"Clean source release: OK\n  - {final_path}")
    print(f"  - SHA-256: {sha256_bytes(final_path.read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
