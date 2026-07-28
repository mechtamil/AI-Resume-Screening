"""Private RecruitOS storage scope and stored-file models."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re

_WORKSPACE_PATTERN = re.compile(r"^[a-f0-9]{32}$")


@dataclass(frozen=True, slots=True)
class StorageScope:
    """Owner-bound filesystem workspace used by one screening session."""

    tenant_id: int
    user_id: int
    workspace_id: str

    def require_valid(self) -> None:
        if int(self.tenant_id or 0) <= 0:
            raise PermissionError("A valid tenant is required for private storage.")
        if int(self.user_id or 0) <= 0:
            raise PermissionError("A valid user is required for private storage.")
        if not _WORKSPACE_PATTERN.fullmatch(str(self.workspace_id or "")):
            raise ValueError("workspace_id must be a 32-character hexadecimal identifier.")

    def summary(self) -> dict[str, int | str]:
        self.require_valid()
        return asdict(self)


@dataclass(frozen=True, slots=True)
class StoredFile:
    """Metadata returned after a private file is stored successfully."""

    asset_id: str
    category: str
    original_name: str
    stored_name: str
    relative_path: str
    absolute_path: Path
    size_bytes: int
    sha256: str

    def summary(self) -> dict[str, str | int]:
        """Return serializable metadata without exposing the server path."""
        return {
            "asset_id": self.asset_id,
            "category": self.category,
            "original_name": self.original_name,
            "stored_name": self.stored_name,
            "relative_path": self.relative_path,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }
