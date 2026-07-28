"""Generate and store user-private RecruitOS report exports."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models.security_context import SecurityContext
from models.storage_asset import StorageScope, StoredFile
from services.secure_storage_service import SecureStorageService


@dataclass(frozen=True, slots=True)
class SecureExport:
    filename: str
    data: bytes
    stored_file: StoredFile


class SecureExportService:
    """Create an Excel report in memory and persist it in the current workspace."""

    def __init__(self, storage: SecureStorageService | None = None, report_builder: Any | None = None) -> None:
        self.storage = storage or SecureStorageService()
        self.report_builder = report_builder

    def build_excel_report(
        self,
        context: SecurityContext,
        scope: StorageScope,
        analysis_result: dict[str, Any],
    ) -> SecureExport:
        context.require_valid()
        scope.require_valid()
        builder = self.report_builder or self._default_report_builder()
        job = analysis_result.get("job_description")
        job_title = str(getattr(job, "job_title", "") or "")
        filename = str(builder.default_filename(job_title))
        data = bytes(builder.build_report(analysis_result))
        stored = self.storage.save_export_bytes(context, scope, filename, data)
        return SecureExport(filename=filename, data=data, stored_file=stored)

    def read_export(self, context: SecurityContext, stored_file: StoredFile) -> bytes:
        return self.storage.read_owned_file(context, stored_file.absolute_path)

    @staticmethod
    def _default_report_builder():
        try:
            from reports.excel_report import ExcelReportService
        except ImportError as exc:
            raise RuntimeError(
                "Sprint 5.7.0 ExcelReportService is required for secure report export."
            ) from exc
        return ExcelReportService
