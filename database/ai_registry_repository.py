"""Persistence for AI models, prompt versions, tenant policies, and telemetry."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from database.database import Database


class AIRegistryRepository:
    """Low-level AI registry persistence without business authorization."""

    def __init__(self, database: Database | str | Path | None = None) -> None:
        self._owns_database = not isinstance(database, Database)
        self.db = database if isinstance(database, Database) else Database(database)
        self.db.create_tables()

    # ------------------------------------------------------------------
    # Model registry
    # ------------------------------------------------------------------

    def create_model(
        self,
        *,
        model_key: str,
        provider_code: str,
        model_name: str,
        display_name: str,
        deployment_type: str,
        supports_structured_output: bool,
        input_cost_per_million_usd: float,
        output_cost_per_million_usd: float,
        context_window: int,
        max_output_tokens: int,
        status: str,
        created_by_user_id: int,
    ) -> dict[str, Any]:
        now = self._utc_now()
        cursor = self.db.connection.execute(
            """
            INSERT INTO ai_model_registry
            (model_key, provider_code, model_name, display_name,
             deployment_type, supports_structured_output,
             input_cost_per_million_usd, output_cost_per_million_usd,
             context_window, max_output_tokens, status,
             created_by_user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(model_key),
                str(provider_code),
                str(model_name),
                str(display_name),
                str(deployment_type),
                int(bool(supports_structured_output)),
                float(input_cost_per_million_usd),
                float(output_cost_per_million_usd),
                int(context_window),
                int(max_output_tokens),
                str(status),
                int(created_by_user_id),
                now,
                now,
            ),
        )
        self.db.connection.commit()
        created = self.get_model(int(cursor.lastrowid))
        if not created:
            raise RuntimeError("AI model could not be reloaded after creation.")
        return created

    def get_model(self, model_id: int) -> dict[str, Any] | None:
        row = self.db.connection.execute(
            "SELECT * FROM ai_model_registry WHERE id = ?",
            (int(model_id),),
        ).fetchone()
        return self._row(row)

    def get_model_by_key(self, model_key: str) -> dict[str, Any] | None:
        row = self.db.connection.execute(
            "SELECT * FROM ai_model_registry WHERE model_key = ?",
            (str(model_key),),
        ).fetchone()
        return self._row(row)

    def list_models(self, *, active_only: bool = False) -> list[dict[str, Any]]:
        where = "WHERE status = 'ACTIVE'" if active_only else ""
        rows = self.db.connection.execute(
            f"""
            SELECT * FROM ai_model_registry
            {where}
            ORDER BY provider_code, display_name, id
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def update_model_status(
        self,
        *,
        model_id: int,
        status: str,
    ) -> dict[str, Any]:
        self.db.connection.execute(
            """
            UPDATE ai_model_registry
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (str(status), self._utc_now(), int(model_id)),
        )
        self.db.connection.commit()
        updated = self.get_model(model_id)
        if not updated:
            raise LookupError("The selected AI model was not found.")
        return updated

    # ------------------------------------------------------------------
    # Prompt registry
    # ------------------------------------------------------------------

    def next_prompt_version(self, prompt_key: str) -> int:
        row = self.db.connection.execute(
            """
            SELECT COALESCE(MAX(version_number), 0) + 1 AS next_version
            FROM ai_prompt_versions
            WHERE prompt_key = ?
            """,
            (str(prompt_key),),
        ).fetchone()
        return int(row["next_version"] if row else 1)

    def create_prompt_version(
        self,
        *,
        prompt_key: str,
        task_code: str,
        version_number: int,
        system_template: str,
        user_template: str,
        output_schema: dict[str, Any],
        status: str,
        created_by_user_id: int,
    ) -> dict[str, Any]:
        now = self._utc_now()
        cursor = self.db.connection.execute(
            """
            INSERT INTO ai_prompt_versions
            (prompt_key, task_code, version_number, system_template,
             user_template, output_schema_json, status,
             created_by_user_id, created_at, activated_by_user_id, activated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, '')
            """,
            (
                str(prompt_key),
                str(task_code),
                int(version_number),
                str(system_template),
                str(user_template),
                json.dumps(output_schema, ensure_ascii=False, sort_keys=True),
                str(status),
                int(created_by_user_id),
                now,
            ),
        )
        self.db.connection.commit()
        created = self.get_prompt_version(int(cursor.lastrowid))
        if not created:
            raise RuntimeError("AI prompt version could not be reloaded after creation.")
        return created

    def get_prompt_version(self, prompt_version_id: int) -> dict[str, Any] | None:
        row = self.db.connection.execute(
            "SELECT * FROM ai_prompt_versions WHERE id = ?",
            (int(prompt_version_id),),
        ).fetchone()
        return self._prompt_row(row)

    def list_prompt_versions(
        self,
        *,
        prompt_key: str | None = None,
        task_code: str | None = None,
        active_only: bool = False,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if prompt_key:
            clauses.append("prompt_key = ?")
            params.append(str(prompt_key))
        if task_code:
            clauses.append("task_code = ?")
            params.append(str(task_code))
        if active_only:
            clauses.append("status = 'ACTIVE'")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.db.connection.execute(
            f"""
            SELECT * FROM ai_prompt_versions
            {where}
            ORDER BY prompt_key, version_number DESC, id DESC
            """,
            tuple(params),
        ).fetchall()
        return [self._prompt_row(row) for row in rows]

    def activate_prompt_version(
        self,
        *,
        prompt_version_id: int,
        activated_by_user_id: int,
    ) -> dict[str, Any]:
        prompt = self.get_prompt_version(prompt_version_id)
        if not prompt:
            raise LookupError("The selected AI prompt version was not found.")
        now = self._utc_now()
        with self.db.transaction():
            self.db.connection.execute(
                """
                UPDATE ai_prompt_versions
                SET status = 'INACTIVE'
                WHERE prompt_key = ? AND status = 'ACTIVE'
                """,
                (str(prompt["prompt_key"]),),
            )
            self.db.connection.execute(
                """
                UPDATE ai_prompt_versions
                SET status = 'ACTIVE', activated_by_user_id = ?, activated_at = ?
                WHERE id = ?
                """,
                (int(activated_by_user_id), now, int(prompt_version_id)),
            )
        activated = self.get_prompt_version(prompt_version_id)
        if not activated:
            raise RuntimeError("Activated AI prompt could not be reloaded.")
        return activated

    # ------------------------------------------------------------------
    # Tenant policy
    # ------------------------------------------------------------------

    def upsert_policy(
        self,
        *,
        tenant_id: int,
        target_user_id: int,
        task_code: str,
        enabled: bool,
        model_id: int,
        prompt_version_id: int,
        allow_external_data: bool,
        max_input_chars: int,
        timeout_seconds: int,
        daily_request_limit: int,
        created_by_user_id: int,
    ) -> dict[str, Any]:
        now = self._utc_now()
        self.db.connection.execute(
            """
            INSERT INTO tenant_ai_policies
            (tenant_id, target_user_id, task_code, enabled,
             model_id, prompt_version_id, allow_external_data,
             max_input_chars, timeout_seconds, daily_request_limit,
             created_by_user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(tenant_id, target_user_id, task_code)
            DO UPDATE SET
                enabled = excluded.enabled,
                model_id = excluded.model_id,
                prompt_version_id = excluded.prompt_version_id,
                allow_external_data = excluded.allow_external_data,
                max_input_chars = excluded.max_input_chars,
                timeout_seconds = excluded.timeout_seconds,
                daily_request_limit = excluded.daily_request_limit,
                created_by_user_id = excluded.created_by_user_id,
                updated_at = excluded.updated_at
            """,
            (
                int(tenant_id),
                int(target_user_id),
                str(task_code),
                int(bool(enabled)),
                int(model_id),
                int(prompt_version_id),
                int(bool(allow_external_data)),
                int(max_input_chars),
                int(timeout_seconds),
                int(daily_request_limit),
                int(created_by_user_id),
                now,
                now,
            ),
        )
        self.db.connection.commit()
        policy = self.get_policy(
            tenant_id=tenant_id,
            target_user_id=target_user_id,
            task_code=task_code,
        )
        if not policy:
            raise RuntimeError("AI policy could not be reloaded after update.")
        return policy

    def get_policy(
        self,
        *,
        tenant_id: int,
        target_user_id: int,
        task_code: str,
    ) -> dict[str, Any] | None:
        row = self.db.connection.execute(
            """
            SELECT p.*,
                   m.model_key, m.provider_code, m.model_name, m.display_name,
                   m.deployment_type, m.supports_structured_output,
                   m.input_cost_per_million_usd,
                   m.output_cost_per_million_usd,
                   m.context_window, m.max_output_tokens,
                   m.status AS model_status,
                   pv.prompt_key, pv.version_number AS prompt_version_number,
                   pv.system_template, pv.user_template, pv.output_schema_json,
                   pv.status AS prompt_status
            FROM tenant_ai_policies p
            JOIN ai_model_registry m ON m.id = p.model_id
            JOIN ai_prompt_versions pv ON pv.id = p.prompt_version_id
            WHERE p.tenant_id = ? AND p.target_user_id = ? AND p.task_code = ?
            LIMIT 1
            """,
            (int(tenant_id), int(target_user_id), str(task_code)),
        ).fetchone()
        return self._policy_row(row)

    def list_policies(
        self,
        *,
        tenant_id: int,
        target_user_id: int,
    ) -> list[dict[str, Any]]:
        rows = self.db.connection.execute(
            """
            SELECT p.*,
                   m.model_key, m.provider_code, m.model_name, m.display_name,
                   m.deployment_type, m.status AS model_status,
                   pv.prompt_key, pv.version_number AS prompt_version_number,
                   pv.status AS prompt_status
            FROM tenant_ai_policies p
            JOIN ai_model_registry m ON m.id = p.model_id
            JOIN ai_prompt_versions pv ON pv.id = p.prompt_version_id
            WHERE p.tenant_id = ? AND p.target_user_id = ?
            ORDER BY p.task_code
            """,
            (int(tenant_id), int(target_user_id)),
        ).fetchall()
        return [self._policy_row(row) for row in rows]

    # ------------------------------------------------------------------
    # Telemetry
    # ------------------------------------------------------------------

    def record_inference_event(
        self,
        *,
        tenant_id: int,
        user_id: int,
        task_code: str,
        provider_code: str,
        model_id: int | None,
        model_key: str,
        prompt_version_id: int | None,
        request_id: str,
        outcome: str,
        latency_ms: int,
        input_chars: int,
        output_chars: int,
        input_tokens: int,
        output_tokens: int,
        estimated_cost_usd: float,
        error_code: str = "",
        error_message_redacted: str = "",
    ) -> int:
        cursor = self.db.connection.execute(
            """
            INSERT INTO ai_inference_events
            (tenant_id, user_id, task_code, provider_code, model_id,
             model_key, prompt_version_id, request_id, outcome,
             latency_ms, input_chars, output_chars, input_tokens,
             output_tokens, estimated_cost_usd, error_code,
             error_message_redacted, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(tenant_id),
                int(user_id),
                str(task_code),
                str(provider_code),
                int(model_id) if model_id else None,
                str(model_key),
                int(prompt_version_id) if prompt_version_id else None,
                str(request_id),
                str(outcome),
                int(latency_ms),
                int(input_chars),
                int(output_chars),
                int(input_tokens),
                int(output_tokens),
                float(estimated_cost_usd),
                str(error_code or ""),
                str(error_message_redacted or ""),
                self._utc_now(),
            ),
        )
        self.db.connection.commit()
        return int(cursor.lastrowid)

    def count_requests_today(self, *, tenant_id: int, user_id: int, task_code: str) -> int:
        row = self.db.connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM ai_inference_events
            WHERE tenant_id = ? AND user_id = ? AND task_code = ?
              AND created_at >= datetime('now', 'start of day')
            """,
            (int(tenant_id), int(user_id), str(task_code)),
        ).fetchone()
        return int(row["total"] if row else 0)

    def list_inference_events(
        self,
        *,
        tenant_id: int,
        user_id: int,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        rows = self.db.connection.execute(
            """
            SELECT id, tenant_id, user_id, task_code, provider_code,
                   model_key, prompt_version_id, request_id, outcome,
                   latency_ms, input_chars, output_chars, input_tokens,
                   output_tokens, estimated_cost_usd, error_code,
                   error_message_redacted, created_at
            FROM ai_inference_events
            WHERE tenant_id = ? AND user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (int(tenant_id), int(user_id), max(1, min(int(limit), 1000))),
        ).fetchall()
        return [dict(row) for row in rows]

    def telemetry_summary(self, *, tenant_id: int, user_id: int) -> dict[str, Any]:
        row = self.db.connection.execute(
            """
            SELECT COUNT(*) AS total_requests,
                   SUM(CASE WHEN outcome = 'SUCCESS' THEN 1 ELSE 0 END) AS successes,
                   SUM(CASE WHEN outcome <> 'SUCCESS' THEN 1 ELSE 0 END) AS failures,
                   COALESCE(AVG(latency_ms), 0) AS average_latency_ms,
                   COALESCE(SUM(input_tokens), 0) AS input_tokens,
                   COALESCE(SUM(output_tokens), 0) AS output_tokens,
                   COALESCE(SUM(estimated_cost_usd), 0) AS estimated_cost_usd
            FROM ai_inference_events
            WHERE tenant_id = ? AND user_id = ?
            """,
            (int(tenant_id), int(user_id)),
        ).fetchone()
        return dict(row) if row else {
            "total_requests": 0,
            "successes": 0,
            "failures": 0,
            "average_latency_ms": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    def close(self) -> None:
        if self._owns_database:
            self.db.close()

    @staticmethod
    def _row(row: Any) -> dict[str, Any] | None:
        return dict(row) if row else None

    @staticmethod
    def _prompt_row(row: Any) -> dict[str, Any] | None:
        if not row:
            return None
        record = dict(row)
        try:
            record["output_schema"] = json.loads(record.get("output_schema_json") or "{}")
        except json.JSONDecodeError:
            record["output_schema"] = {}
        return record

    @staticmethod
    def _policy_row(row: Any) -> dict[str, Any] | None:
        if not row:
            return None
        record = dict(row)
        if "output_schema_json" in record:
            try:
                record["output_schema"] = json.loads(
                    record.get("output_schema_json") or "{}"
                )
            except json.JSONDecodeError:
                record["output_schema"] = {}
        return record

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")
