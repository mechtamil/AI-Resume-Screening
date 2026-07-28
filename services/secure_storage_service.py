"""Tenant- and user-isolated filesystem storage for RecruitOS.

The service never accepts an arbitrary destination directory from the caller.
Every path is derived from the authenticated :class:`SecurityContext` and a
server-generated workspace identifier. Ownership checks are repeated for reads,
deletes and listings so a guessed path cannot cross user boundaries.
"""
from __future__ import annotations

import hashlib
import re
import shutil
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from config.paths import PRIVATE_OUTPUT_DIR, PRIVATE_TEMP_DIR, PRIVATE_UPLOADS_DIR
from models.security_context import SecurityContext
from models.storage_asset import StorageScope, StoredFile
from utils.file_utils import validate


class SecureStorageService:
    """Private filesystem boundary for uploads, temporary files and exports."""

    UPLOAD_CATEGORIES = frozenset({"job_description", "resumes", "skill_lists"})
    PRIVATE_CATEGORIES = frozenset({"job_description", "resumes", "skill_lists", "temp", "reports"})

    def __init__(
        self,
        *,
        uploads_root: str | Path | None = None,
        temp_root: str | Path | None = None,
        output_root: str | Path | None = None,
    ) -> None:
        self.uploads_root = Path(uploads_root or PRIVATE_UPLOADS_DIR).resolve()
        self.temp_root = Path(temp_root or PRIVATE_TEMP_DIR).resolve()
        self.output_root = Path(output_root or PRIVATE_OUTPUT_DIR).resolve()
        for root in (self.uploads_root, self.temp_root, self.output_root):
            root.mkdir(parents=True, exist_ok=True)
            self._reject_symlink(root)

    @staticmethod
    def create_scope(context: SecurityContext, workspace_id: str | None = None) -> StorageScope:
        context.require_valid()
        scope = StorageScope(
            tenant_id=int(context.tenant_id),
            user_id=int(context.user_id),
            workspace_id=str(workspace_id or uuid4().hex).lower(),
        )
        scope.require_valid()
        return scope

    @classmethod
    def safe_filename(cls, raw_name: str, *, fallback: str = "file") -> str:
        """Return a display-safe filename without directory components."""
        base = Path(str(raw_name or fallback)).name
        stem = re.sub(r"[^A-Za-z0-9._ -]+", "_", Path(base).stem)
        stem = re.sub(r"\s+", " ", stem).strip(" ._") or fallback
        suffix = re.sub(r"[^A-Za-z0-9.]", "", Path(base).suffix.lower())
        return f"{stem[:120]}{suffix}"

    def save_upload(
        self,
        context: SecurityContext,
        scope: StorageScope,
        category: str,
        uploaded_file,
        allowed_extensions: tuple[str, ...],
    ) -> StoredFile:
        self._require_scope_owner(context, scope)
        normalized_category = self._normalize_category(category, self.UPLOAD_CATEGORIES)
        if uploaded_file is None:
            raise ValueError("An uploaded file is required.")

        errors = validate(uploaded_file, allowed_extensions)
        if errors:
            raise ValueError("; ".join(errors))

        content = bytes(uploaded_file.getbuffer())
        original_name = self.safe_filename(getattr(uploaded_file, "name", "upload"), fallback="upload")
        return self._store_bytes(
            context,
            scope,
            root=self.uploads_root,
            category=normalized_category,
            original_name=original_name,
            content=content,
        )

    def save_temp_bytes(
        self,
        context: SecurityContext,
        scope: StorageScope,
        filename: str,
        content: bytes,
    ) -> StoredFile:
        self._require_scope_owner(context, scope)
        return self._store_bytes(
            context,
            scope,
            root=self.temp_root,
            category="temp",
            original_name=self.safe_filename(filename, fallback="temporary"),
            content=bytes(content),
        )

    def save_export_bytes(
        self,
        context: SecurityContext,
        scope: StorageScope,
        filename: str,
        content: bytes,
    ) -> StoredFile:
        self._require_scope_owner(context, scope)
        return self._store_bytes(
            context,
            scope,
            root=self.output_root,
            category="reports",
            original_name=self.safe_filename(filename, fallback="RecruitOS_Report.xlsx"),
            content=bytes(content),
        )

    def read_owned_file(self, context: SecurityContext, path: str | Path) -> bytes:
        resolved = self.require_owned_path(context, path)
        if not resolved.is_file():
            raise FileNotFoundError("The requested private file is not available.")
        return resolved.read_bytes()

    def delete_owned_file(self, context: SecurityContext, path: str | Path) -> bool:
        resolved = self.require_owned_path(context, path)
        if not resolved.exists():
            return False
        if not resolved.is_file():
            raise IsADirectoryError("Only a private file can be deleted by this operation.")
        resolved.unlink()
        return True

    def list_workspace_files(
        self,
        context: SecurityContext,
        scope: StorageScope,
        *,
        include_temp: bool = False,
    ) -> list[Path]:
        self._require_scope_owner(context, scope)
        roots = [self.uploads_root, self.output_root]
        if include_temp:
            roots.append(self.temp_root)
        files: list[Path] = []
        for root in roots:
            workspace = self._workspace_root(root, scope)
            if workspace.exists():
                files.extend(path for path in workspace.rglob("*") if path.is_file())
        return sorted(files)

    def cleanup_temp_workspace(self, context: SecurityContext, scope: StorageScope) -> None:
        self._require_scope_owner(context, scope)
        workspace = self._workspace_root(self.temp_root, scope)
        if workspace.exists():
            shutil.rmtree(workspace)

    def delete_workspace(self, context: SecurityContext, scope: StorageScope) -> None:
        """Delete only the authenticated user's specified workspace."""
        self._require_scope_owner(context, scope)
        for root in (self.uploads_root, self.temp_root, self.output_root):
            workspace = self._workspace_root(root, scope)
            if workspace.exists():
                shutil.rmtree(workspace)

    def require_owned_path(self, context: SecurityContext, path: str | Path) -> Path:
        """Resolve a path and reject access outside the current user's roots."""
        context.require_valid()
        candidate = Path(path).resolve(strict=False)
        allowed_user_roots = [
            self._user_root(root, context)
            for root in (self.uploads_root, self.temp_root, self.output_root)
        ]
        if not any(self._is_relative_to(candidate, root) for root in allowed_user_roots):
            raise PermissionError("The requested file does not belong to the authenticated user.")
        self._reject_symlink_chain(candidate)
        return candidate

    def _store_bytes(
        self,
        context: SecurityContext,
        scope: StorageScope,
        *,
        root: Path,
        category: str,
        original_name: str,
        content: bytes,
    ) -> StoredFile:
        self._require_scope_owner(context, scope)
        if not isinstance(content, (bytes, bytearray)):
            raise TypeError("Stored content must be bytes.")
        category = self._normalize_category(category, self.PRIVATE_CATEGORIES)
        directory = self._workspace_root(root, scope) / category
        directory.mkdir(parents=True, exist_ok=True)
        self._reject_symlink_chain(directory)

        asset_id = uuid4().hex
        safe_name = self.safe_filename(original_name)
        destination = (directory / f"{asset_id}_{safe_name}").resolve(strict=False)
        self._require_within(destination, directory)
        destination.write_bytes(bytes(content))

        digest = hashlib.sha256(bytes(content)).hexdigest()
        relative = destination.relative_to(root).as_posix()
        return StoredFile(
            asset_id=asset_id,
            category=category,
            original_name=safe_name,
            stored_name=destination.name,
            relative_path=relative,
            absolute_path=destination,
            size_bytes=len(content),
            sha256=digest,
        )

    def _require_scope_owner(self, context: SecurityContext, scope: StorageScope) -> None:
        context.require_valid()
        scope.require_valid()
        if int(scope.tenant_id) != int(context.tenant_id) or int(scope.user_id) != int(context.user_id):
            raise PermissionError("The storage workspace does not belong to the authenticated user.")

    @staticmethod
    def _normalize_category(category: str, allowed: Iterable[str]) -> str:
        value = str(category or "").strip().casefold()
        if value not in set(allowed):
            raise ValueError(f"Unsupported private storage category: {category!r}")
        return value

    def _workspace_root(self, root: Path, scope: StorageScope) -> Path:
        workspace = (
            root
            / f"tenant_{int(scope.tenant_id)}"
            / f"user_{int(scope.user_id)}"
            / f"workspace_{scope.workspace_id}"
        ).resolve(strict=False)
        self._require_within(workspace, root)
        return workspace

    def _user_root(self, root: Path, context: SecurityContext) -> Path:
        user_root = (
            root
            / f"tenant_{int(context.tenant_id)}"
            / f"user_{int(context.user_id)}"
        ).resolve(strict=False)
        self._require_within(user_root, root)
        return user_root

    @classmethod
    def _require_within(cls, candidate: Path, parent: Path) -> None:
        if not cls._is_relative_to(candidate.resolve(strict=False), parent.resolve(strict=False)):
            raise PermissionError("Private storage path escaped its authorized root.")

    @staticmethod
    def _is_relative_to(candidate: Path, parent: Path) -> bool:
        try:
            candidate.relative_to(parent)
            return True
        except ValueError:
            return False

    @staticmethod
    def _reject_symlink(path: Path) -> None:
        if path.exists() and path.is_symlink():
            raise PermissionError("Symbolic links are not allowed in private storage roots.")

    @classmethod
    def _reject_symlink_chain(cls, path: Path) -> None:
        current = path
        while True:
            cls._reject_symlink(current)
            if current.parent == current:
                break
            current = current.parent
