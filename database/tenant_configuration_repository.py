"""Persistence for immutable tenant configuration workbook versions."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from database.database import Database


class TenantConfigurationRepository:
    """Low-level configuration-version persistence.

    Authorization belongs to :mod:`services.tenant_configuration_service`. This
    repository never exposes records across tenant identifiers accidentally.
    """

    def __init__(self, database: Database | str | Path | None = None) -> None:
        self._owns_database = not isinstance(database, Database)
        self.db = database if isinstance(database, Database) else Database(database)
        self.db.create_tables()

    def next_version_number(self, tenant_id: int) -> int:
        row = self.db.connection.execute(
            """
            SELECT COALESCE(MAX(version_number), 0) + 1 AS next_version
            FROM tenant_configuration_versions
            WHERE tenant_id = ?
            """,
            (int(tenant_id),),
        ).fetchone()
        return int(row["next_version"] if row else 1)

    def find_by_hash(self, tenant_id: int, file_sha256: str) -> dict[str, Any] | None:
        row = self.db.connection.execute(
            """
            SELECT * FROM tenant_configuration_versions
            WHERE tenant_id = ? AND file_sha256 = ?
            LIMIT 1
            """,
            (int(tenant_id), str(file_sha256)),
        ).fetchone()
        return self._row(row)

    def create_version(
        self,
        *,
        tenant_id: int,
        configuration_key: str,
        version_number: int,
        source_name: str,
        file_path: str,
        file_sha256: str,
        file_size: int,
        validation: dict[str, Any],
        created_by_user_id: int,
    ) -> dict[str, Any]:
        cursor = self.db.connection.execute(
            """
            INSERT INTO tenant_configuration_versions
            (tenant_id, configuration_key, version_number, source_name,
             file_path, file_sha256, file_size, validation_json, status,
             created_by_user_id, created_at, activated_by_user_id, activated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'DRAFT', ?, ?, NULL, '')
            """,
            (
                int(tenant_id),
                str(configuration_key),
                int(version_number),
                str(source_name),
                str(file_path),
                str(file_sha256),
                int(file_size),
                self._dump(validation),
                int(created_by_user_id),
                self._utc_now(),
            ),
        )
        self.db.connection.commit()
        created = self.get_version(int(tenant_id), int(cursor.lastrowid))
        if not created:
            raise RuntimeError("Configuration version could not be reloaded after creation.")
        return created

    def activate_version(
        self,
        *,
        tenant_id: int,
        version_id: int,
        activated_by_user_id: int,
    ) -> dict[str, Any]:
        if not self.get_version(tenant_id, version_id):
            raise LookupError("The requested configuration version was not found.")
        now = self._utc_now()
        with self.db.transaction():
            self.db.connection.execute(
                """
                UPDATE tenant_configuration_versions
                SET status = 'INACTIVE'
                WHERE tenant_id = ? AND status = 'ACTIVE'
                """,
                (int(tenant_id),),
            )
            self.db.connection.execute(
                """
                UPDATE tenant_configuration_versions
                SET status = 'ACTIVE', activated_by_user_id = ?, activated_at = ?
                WHERE tenant_id = ? AND id = ?
                """,
                (
                    int(activated_by_user_id),
                    now,
                    int(tenant_id),
                    int(version_id),
                ),
            )
        active = self.get_version(tenant_id, version_id)
        if not active:
            raise RuntimeError("Configuration activation could not be confirmed.")
        return active

    def use_system_default(self, tenant_id: int) -> None:
        self.db.connection.execute(
            """
            UPDATE tenant_configuration_versions
            SET status = CASE WHEN status = 'ACTIVE' THEN 'INACTIVE' ELSE status END
            WHERE tenant_id = ?
            """,
            (int(tenant_id),),
        )
        self.db.connection.commit()

    def get_active_version(self, tenant_id: int) -> dict[str, Any] | None:
        row = self.db.connection.execute(
            """
            SELECT * FROM tenant_configuration_versions
            WHERE tenant_id = ? AND status = 'ACTIVE'
            ORDER BY activated_at DESC, id DESC
            LIMIT 1
            """,
            (int(tenant_id),),
        ).fetchone()
        return self._row(row)

    def get_version(self, tenant_id: int, version_id: int) -> dict[str, Any] | None:
        row = self.db.connection.execute(
            """
            SELECT * FROM tenant_configuration_versions
            WHERE tenant_id = ? AND id = ?
            LIMIT 1
            """,
            (int(tenant_id), int(version_id)),
        ).fetchone()
        return self._row(row)

    def list_versions(self, tenant_id: int) -> list[dict[str, Any]]:
        rows = self.db.connection.execute(
            """
            SELECT * FROM tenant_configuration_versions
            WHERE tenant_id = ?
            ORDER BY version_number DESC, id DESC
            """,
            (int(tenant_id),),
        ).fetchall()
        return [self._row(row) for row in rows if row is not None]

    def close(self) -> None:
        if self._owns_database:
            self.db.close()

    @classmethod
    def _row(cls, row: Any) -> dict[str, Any] | None:
        if row is None:
            return None
        data = dict(row)
        data["validation"] = cls._load(data.pop("validation_json", "{}"), {})
        return data

    @staticmethod
    def _dump(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)

    @staticmethod
    def _load(value: Any, default: Any) -> Any:
        try:
            return json.loads(str(value or ""))
        except (TypeError, ValueError, json.JSONDecodeError):
            return default

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")
