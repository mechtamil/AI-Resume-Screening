"""Authenticated upload facade backed by private RecruitOS storage."""
from __future__ import annotations

from pathlib import Path

from config.settings import SUPPORTED_JD_TYPES, SUPPORTED_RESUME_TYPES, SUPPORTED_SKILL_TYPES
from models.security_context import SecurityContext
from models.storage_asset import StorageScope, StoredFile
from services.secure_storage_service import SecureStorageService


class UploadService:
    """Store recruitment uploads only inside the current user's workspace."""

    _storage = SecureStorageService()

    @classmethod
    def configure_storage(cls, storage: SecureStorageService) -> None:
        """Inject an isolated storage instance, primarily for tests."""
        if not isinstance(storage, SecureStorageService):
            raise TypeError("storage must be a SecureStorageService.")
        cls._storage = storage

    @classmethod
    def reset_storage(cls) -> None:
        """Restore the production private-storage configuration."""
        cls._storage = SecureStorageService()

    @staticmethod
    def create_workspace(context: SecurityContext, workspace_id: str | None = None) -> StorageScope:
        return SecureStorageService.create_scope(context, workspace_id)

    @staticmethod
    def _safe_name(name: str) -> str:
        """Backward-compatible filename sanitizer used by earlier tests."""
        return SecureStorageService.safe_filename(name)

    @classmethod
    def save_job_description(
        cls,
        context: SecurityContext,
        scope: StorageScope,
        uploaded_file,
    ) -> StoredFile:
        return cls._storage.save_upload(
            context,
            scope,
            "job_description",
            uploaded_file,
            SUPPORTED_JD_TYPES,
        )

    @classmethod
    def save_skill_list(
        cls,
        context: SecurityContext,
        scope: StorageScope,
        uploaded_file,
    ) -> StoredFile:
        return cls._storage.save_upload(
            context,
            scope,
            "skill_lists",
            uploaded_file,
            SUPPORTED_SKILL_TYPES,
        )

    @classmethod
    def save_resume(
        cls,
        context: SecurityContext,
        scope: StorageScope,
        uploaded_file,
    ) -> StoredFile:
        return cls._storage.save_upload(
            context,
            scope,
            "resumes",
            uploaded_file,
            SUPPORTED_RESUME_TYPES,
        )

    @classmethod
    def save_multiple_resumes(
        cls,
        context: SecurityContext,
        scope: StorageScope,
        uploaded_files,
    ) -> list[StoredFile]:
        return [
            cls.save_resume(context, scope, item)
            for item in (uploaded_files or [])
        ]

    @classmethod
    def delete_workspace(cls, context: SecurityContext, scope: StorageScope) -> None:
        cls._storage.delete_workspace(context, scope)

    @classmethod
    def cleanup_temp_workspace(cls, context: SecurityContext, scope: StorageScope) -> None:
        cls._storage.cleanup_temp_workspace(context, scope)

    @classmethod
    def read_owned_file(cls, context: SecurityContext, path: str | Path) -> bytes:
        return cls._storage.read_owned_file(context, path)
