"""Tenant-scoped, immutable RecruitOS configuration management."""
from __future__ import annotations

import json
import os
import re
from hashlib import sha256
from pathlib import Path
from shutil import move
from typing import Any
from uuid import uuid4

from config.paths import CONFIGURATION_WORKBOOK, PRIVATE_CONFIGURATIONS_DIR
from database.tenant_configuration_repository import TenantConfigurationRepository
from database.user_repository import UserRepository
from models.configuration_version import ConfigurationSelection
from models.security_context import SecurityContext
from services.authorization_service import (
    PERMISSION_CONFIGURATION_MANAGE_GLOBAL,
    PERMISSION_CONFIGURATION_MANAGE_TENANT,
    PERMISSION_CONFIGURATION_VIEW,
    AuthorizationService,
)
from services.configuration_context import ConfigurationContext
from services.configuration_validator import ConfigurationValidator
from services.master_repository import MasterRepository


class TenantConfigurationService:
    """Manage validated workbook versions without cross-tenant cache leakage."""

    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

    def __init__(
        self,
        database_path: str | Path | None = None,
        *,
        private_root: str | Path | None = None,
        system_default_path: str | Path | None = None,
    ) -> None:
        self.database_path = database_path
        self.private_root = Path(private_root or PRIVATE_CONFIGURATIONS_DIR).resolve()
        self.system_default_path = Path(
            system_default_path or CONFIGURATION_WORKBOOK
        ).resolve()
        self.private_root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Resolution and health
    # ------------------------------------------------------------------

    def resolve_active(self, context: SecurityContext) -> ConfigurationSelection:
        """Resolve only the authenticated user's active workspace configuration."""
        context.require_valid()
        repository = TenantConfigurationRepository(self.database_path)
        try:
            active = repository.get_active_version(context.tenant_id)
        finally:
            repository.close()
        return self._selection_from_record(context.tenant_id, active)

    def resolve_for_user(
        self,
        context: SecurityContext,
        target_user_id: int,
    ) -> ConfigurationSelection:
        target = self._target_user(context, target_user_id, manage=False)
        repository = TenantConfigurationRepository(self.database_path)
        try:
            active = repository.get_active_version(int(target["tenant_id"]))
        finally:
            repository.close()
        return self._selection_from_record(int(target["tenant_id"]), active)

    def configuration_health(
        self,
        context: SecurityContext,
        target_user_id: int | None = None,
    ) -> dict[str, Any]:
        selection = (
            self.resolve_active(context)
            if target_user_id is None or int(target_user_id) == context.user_id
            else self.resolve_for_user(context, int(target_user_id))
        )
        with ConfigurationContext.activate(selection):
            report = ConfigurationValidator.validate()
        return {"selection": selection.summary(), "validation": report}

    def snapshot_for_screening(self, context: SecurityContext) -> tuple[
        ConfigurationSelection,
        dict[str, Any],
    ]:
        selection = self.resolve_active(context)
        with ConfigurationContext.activate(selection):
            validation = ConfigurationValidator.validate_or_raise()
            sheet_summary = MasterRepository.workbook_info()
        selection = ConfigurationSelection(
            tenant_id=selection.tenant_id,
            workbook_path=selection.workbook_path,
            source=selection.source,
            version_id=selection.version_id,
            version_number=selection.version_number,
            configuration_key=selection.configuration_key,
            sha256=selection.sha256,
            file_size=selection.file_size,
            activated_at=selection.activated_at,
            sheet_summary=sheet_summary,
        )
        snapshot = {
            **selection.summary(),
            "validation": {
                "valid": bool(validation["valid"]),
                "warnings": list(validation.get("warnings") or []),
            },
        }
        return selection, snapshot

    # ------------------------------------------------------------------
    # Version administration
    # ------------------------------------------------------------------

    def list_versions(
        self,
        context: SecurityContext,
        target_user_id: int | None = None,
    ) -> list[dict[str, Any]]:
        target = self._target_user(
            context,
            target_user_id or context.user_id,
            manage=False,
        )
        repository = TenantConfigurationRepository(self.database_path)
        try:
            return repository.list_versions(int(target["tenant_id"]))
        finally:
            repository.close()

    def upload_version(
        self,
        context: SecurityContext,
        *,
        target_user_id: int,
        file_name: str,
        content: bytes,
        activate: bool = False,
    ) -> dict[str, Any]:
        target = self._target_user(context, target_user_id, manage=True)
        payload = bytes(content or b"")
        source_name = self._safe_source_name(file_name)
        if Path(source_name).suffix.casefold() != ".xlsx":
            raise ValueError("Tenant configuration must be an .xlsx workbook.")
        if not payload:
            raise ValueError("The uploaded configuration workbook is empty.")
        if len(payload) > self.MAX_FILE_SIZE_BYTES:
            raise ValueError("The configuration workbook exceeds the 10 MB limit.")

        tenant_id = int(target["tenant_id"])
        digest = sha256(payload).hexdigest()
        repository = TenantConfigurationRepository(self.database_path)
        try:
            duplicate = repository.find_by_hash(tenant_id, digest)
            if duplicate:
                raise ValueError(
                    f"This workbook already exists as configuration version "
                    f"{duplicate['version_number']}."
                )

            version_number = repository.next_version_number(tenant_id)
            configuration_key = uuid4().hex
            tenant_root = self._tenant_root(tenant_id)
            staging = tenant_root / ".staging"
            staging.mkdir(parents=True, exist_ok=True)
            temporary_path = staging / f"{configuration_key}.xlsx"
            temporary_path.write_bytes(payload)

            try:
                report = ConfigurationValidator.validate(temporary_path)
                if not report["valid"]:
                    raise ValueError(
                        "Invalid tenant configuration:\n- "
                        + "\n- ".join(report["errors"])
                    )

                version_root = tenant_root / (
                    f"version_{version_number:04d}_{configuration_key[:8]}"
                )
                version_root.mkdir(parents=True, exist_ok=False)
                final_path = version_root / "RecruitOS_Configuration.xlsx"
                move(str(temporary_path), str(final_path))
                self._make_read_only(final_path)

                stored_validation = {
                    "valid": True,
                    "warnings": list(report.get("warnings") or []),
                    "sheets": dict(report.get("sheets") or {}),
                }
                created = repository.create_version(
                    tenant_id=tenant_id,
                    configuration_key=configuration_key,
                    version_number=version_number,
                    source_name=source_name,
                    file_path=str(final_path),
                    file_sha256=digest,
                    file_size=len(payload),
                    validation=stored_validation,
                    created_by_user_id=context.user_id,
                )
            except Exception:
                temporary_path.unlink(missing_ok=True)
                raise

            self._audit(
                context,
                action="TENANT_CONFIGURATION_UPLOADED",
                target_id=str(created["id"]),
                details={
                    "target_user_id": int(target["id"]),
                    "target_tenant_id": tenant_id,
                    "version_number": version_number,
                    "sha256": digest,
                    "source_name": source_name,
                },
            )
            if activate:
                return self.activate_version(
                    context,
                    target_user_id=int(target["id"]),
                    version_id=int(created["id"]),
                )
            return created
        finally:
            repository.close()

    def activate_version(
        self,
        context: SecurityContext,
        *,
        target_user_id: int,
        version_id: int,
    ) -> dict[str, Any]:
        target = self._target_user(context, target_user_id, manage=True)
        tenant_id = int(target["tenant_id"])
        repository = TenantConfigurationRepository(self.database_path)
        try:
            record = repository.get_version(tenant_id, int(version_id))
            if not record:
                raise LookupError("The selected configuration version is not available.")
            path = self._safe_version_path(tenant_id, record["file_path"])
            digest = self._file_sha256(path)
            if digest != str(record["file_sha256"]):
                raise ValueError(
                    "Configuration integrity check failed. Upload a new version instead."
                )
            report = ConfigurationValidator.validate_or_raise(path)
            active = repository.activate_version(
                tenant_id=tenant_id,
                version_id=int(version_id),
                activated_by_user_id=context.user_id,
            )
            MasterRepository.reload(path)
            self._audit(
                context,
                action="TENANT_CONFIGURATION_ACTIVATED",
                target_id=str(version_id),
                details={
                    "target_user_id": int(target["id"]),
                    "target_tenant_id": tenant_id,
                    "version_number": int(active["version_number"]),
                    "sha256": digest,
                    "warnings": list(report.get("warnings") or []),
                },
            )
            return active
        finally:
            repository.close()

    def use_system_default(
        self,
        context: SecurityContext,
        *,
        target_user_id: int,
    ) -> ConfigurationSelection:
        target = self._target_user(context, target_user_id, manage=True)
        tenant_id = int(target["tenant_id"])
        repository = TenantConfigurationRepository(self.database_path)
        try:
            repository.use_system_default(tenant_id)
        finally:
            repository.close()
        selection = self._system_default_selection(tenant_id)
        self._audit(
            context,
            action="TENANT_CONFIGURATION_REVERTED_TO_SYSTEM_DEFAULT",
            target_id=str(target_user_id),
            details={"target_tenant_id": tenant_id, "sha256": selection.sha256},
        )
        return selection

    def download_version(
        self,
        context: SecurityContext,
        *,
        target_user_id: int,
        version_id: int | None = None,
    ) -> tuple[str, bytes]:
        target = self._target_user(context, target_user_id, manage=False)
        tenant_id = int(target["tenant_id"])
        if version_id is None:
            selection = self._selection_for_tenant(tenant_id)
            name = (
                "RecruitOS_System_Default_Configuration.xlsx"
                if selection.source == "system_default"
                else f"RecruitOS_Configuration_v{selection.version_number}.xlsx"
            )
            return name, Path(selection.workbook_path).read_bytes()

        repository = TenantConfigurationRepository(self.database_path)
        try:
            record = repository.get_version(tenant_id, int(version_id))
        finally:
            repository.close()
        if not record:
            raise LookupError("The selected configuration version is not available.")
        path = self._safe_version_path(tenant_id, record["file_path"])
        return f"RecruitOS_Configuration_v{record['version_number']}.xlsx", path.read_bytes()

    # ------------------------------------------------------------------
    # Authorization and path safety
    # ------------------------------------------------------------------

    def _target_user(
        self,
        context: SecurityContext,
        target_user_id: int,
        *,
        manage: bool,
    ) -> dict[str, Any]:
        context.require_valid()
        if manage:
            if not (
                AuthorizationService.has_permission(
                    context, PERMISSION_CONFIGURATION_MANAGE_GLOBAL
                )
                or AuthorizationService.has_permission(
                    context, PERMISSION_CONFIGURATION_MANAGE_TENANT
                )
            ):
                raise PermissionError("This role cannot manage configuration versions.")
        else:
            AuthorizationService.require_permission(
                context, PERMISSION_CONFIGURATION_VIEW
            )

        users = UserRepository(self.database_path)
        try:
            target = users.get_user_by_id(int(target_user_id))
        finally:
            users.close()
        if not target:
            raise LookupError("The selected RecruitOS user was not found.")

        if int(target["id"]) == context.user_id:
            return target
        if not manage:
            # Configuration metadata for another private workspace is an admin
            # operation even when the caller has basic view permission.
            manage = True
        decision = AuthorizationService.can_manage_target(
            context,
            target_role=str(target.get("role_code") or "USER"),
            target_country_location=str(target.get("country_location") or ""),
        )
        if not decision.allowed:
            raise PermissionError(decision.reason)
        return target

    def _selection_for_tenant(self, tenant_id: int) -> ConfigurationSelection:
        repository = TenantConfigurationRepository(self.database_path)
        try:
            active = repository.get_active_version(int(tenant_id))
        finally:
            repository.close()
        return self._selection_from_record(int(tenant_id), active)

    def _selection_from_record(
        self,
        tenant_id: int,
        record: dict[str, Any] | None,
    ) -> ConfigurationSelection:
        if not record:
            return self._system_default_selection(tenant_id)
        path = self._safe_version_path(tenant_id, record["file_path"])
        digest = self._file_sha256(path)
        if digest != str(record["file_sha256"]):
            raise ValueError(
                "The active tenant configuration failed its integrity check."
            )
        return ConfigurationSelection(
            tenant_id=int(tenant_id),
            workbook_path=path,
            source="tenant_version",
            version_id=int(record["id"]),
            version_number=int(record["version_number"]),
            configuration_key=str(record["configuration_key"]),
            sha256=digest,
            file_size=int(record["file_size"] or path.stat().st_size),
            activated_at=str(record.get("activated_at") or ""),
            sheet_summary=dict((record.get("validation") or {}).get("sheets") or {}),
        )

    def _system_default_selection(self, tenant_id: int) -> ConfigurationSelection:
        if not self.system_default_path.is_file():
            raise FileNotFoundError(
                f"System configuration workbook not found: {self.system_default_path}"
            )
        report = ConfigurationValidator.validate_or_raise(self.system_default_path)
        return ConfigurationSelection(
            tenant_id=int(tenant_id),
            workbook_path=self.system_default_path,
            source="system_default",
            configuration_key="system-default",
            sha256=self._file_sha256(self.system_default_path),
            file_size=self.system_default_path.stat().st_size,
            sheet_summary=dict(report.get("sheets") or {}),
        )

    def _tenant_root(self, tenant_id: int) -> Path:
        root = (self.private_root / f"tenant_{int(tenant_id)}").resolve()
        if not root.is_relative_to(self.private_root):
            raise PermissionError("Invalid tenant configuration path.")
        root.mkdir(parents=True, exist_ok=True)
        return root

    def _safe_version_path(self, tenant_id: int, raw_path: str | Path) -> Path:
        root = self._tenant_root(tenant_id)
        path = Path(raw_path).expanduser().resolve()
        if not path.is_file() or not path.is_relative_to(root):
            raise PermissionError("Configuration file is outside the tenant workspace.")
        if path.is_symlink():
            raise PermissionError("Symbolic links are not permitted for configuration files.")
        return path

    @staticmethod
    def _safe_source_name(file_name: str) -> str:
        name = Path(str(file_name or "configuration.xlsx")).name
        name = re.sub(r"[^A-Za-z0-9._ -]+", "_", name).strip(" .")
        return name or "configuration.xlsx"

    @staticmethod
    def _make_read_only(path: Path) -> None:
        try:
            os.chmod(path, 0o444)
        except OSError:
            # Some hosted filesystems do not support Unix-style permissions.
            pass

    @staticmethod
    def _file_sha256(path: Path) -> str:
        digest = sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _audit(
        self,
        context: SecurityContext,
        *,
        action: str,
        target_id: str,
        details: dict[str, Any],
    ) -> None:
        repository = UserRepository(self.database_path)
        try:
            repository.audit_event(
                tenant_id=context.tenant_id,
                actor_user_id=context.user_id,
                action=action,
                target_type="tenant_configuration",
                target_id=target_id,
                details=details,
            )
        finally:
            repository.close()
