"""Authorized administration of AI models, prompts, policies, and telemetry."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from config.settings import (
    AI_DEFAULT_DAILY_REQUEST_LIMIT,
    AI_DEFAULT_MAX_INPUT_CHARS,
    AI_HTTP_TIMEOUT_SECONDS,
    AI_OLLAMA_BASE_URL,
    AI_OPENAI_API_KEY,
    AI_OPENAI_BASE_URL,
)
from database.ai_registry_repository import AIRegistryRepository
from database.user_repository import UserRepository
from models.security_context import SecurityContext
from services.ai.schema_validator import validate_schema_definition
from services.authorization_service import (
    PERMISSION_AI_POLICY_MANAGE_GLOBAL,
    PERMISSION_AI_POLICY_MANAGE_TENANT,
    PERMISSION_AI_POLICY_VIEW,
    AuthorizationService,
)

_PROVIDER_TYPES = {
    "OPENAI": "HOSTED",
    "OLLAMA": "LOCAL",
}
_VALID_MODEL_STATUS = {"ACTIVE", "INACTIVE"}
_VALID_PROMPT_STATUS = {"DRAFT", "ACTIVE", "INACTIVE"}
_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]{1,127}$")


class AIRegistryService:
    """Manage AI registry metadata without persisting provider credentials."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = database_path

    # ------------------------------------------------------------------
    # Provider readiness
    # ------------------------------------------------------------------

    @staticmethod
    def provider_readiness() -> list[dict[str, Any]]:
        """Return non-secret deployment readiness only."""
        return [
            {
                "provider_code": "OPENAI",
                "deployment_type": "HOSTED",
                "configured": bool(AI_OPENAI_API_KEY and AI_OPENAI_BASE_URL),
                "endpoint": _safe_endpoint_label(AI_OPENAI_BASE_URL),
                "credential": "Configured" if AI_OPENAI_API_KEY else "Missing",
            },
            {
                "provider_code": "OLLAMA",
                "deployment_type": "LOCAL",
                "configured": bool(AI_OLLAMA_BASE_URL),
                "endpoint": _safe_endpoint_label(AI_OLLAMA_BASE_URL),
                "credential": "Not required",
            },
        ]

    # ------------------------------------------------------------------
    # Models
    # ------------------------------------------------------------------

    def list_models(
        self,
        context: SecurityContext,
        *,
        active_only: bool = False,
    ) -> list[dict[str, Any]]:
        AuthorizationService.require_permission(context, PERMISSION_AI_POLICY_VIEW)
        repository = AIRegistryRepository(self.database_path)
        try:
            return repository.list_models(active_only=active_only)
        finally:
            repository.close()

    def register_model(
        self,
        context: SecurityContext,
        *,
        model_key: str,
        provider_code: str,
        model_name: str,
        display_name: str,
        supports_structured_output: bool = True,
        input_cost_per_million_usd: float = 0.0,
        output_cost_per_million_usd: float = 0.0,
        context_window: int = 0,
        max_output_tokens: int = 0,
        status: str = "ACTIVE",
    ) -> dict[str, Any]:
        self._require_registry_management(context)
        key = str(model_key or "").strip().casefold()
        provider = str(provider_code or "").strip().upper()
        name = str(model_name or "").strip()
        label = str(display_name or name).strip()
        status_value = str(status or "ACTIVE").strip().upper()
        if not _KEY_PATTERN.fullmatch(key):
            raise ValueError(
                "Model key must start with a lowercase letter and contain only "
                "lowercase letters, numbers, dots, hyphens, or underscores."
            )
        if provider not in _PROVIDER_TYPES:
            raise ValueError("Provider must be OPENAI or OLLAMA.")
        if not name or len(name) > 200:
            raise ValueError("A provider model name of up to 200 characters is required.")
        if not label or len(label) > 200:
            raise ValueError("A model display name of up to 200 characters is required.")
        if status_value not in _VALID_MODEL_STATUS:
            raise ValueError("Model status must be ACTIVE or INACTIVE.")
        if not supports_structured_output:
            raise ValueError(
                "RecruitOS 5.7.2A registers only models that support structured output."
            )
        input_cost = _non_negative_float(
            input_cost_per_million_usd,
            "Input cost",
        )
        output_cost = _non_negative_float(
            output_cost_per_million_usd,
            "Output cost",
        )
        context_limit = _non_negative_int(context_window, "Context window")
        output_limit = _non_negative_int(max_output_tokens, "Maximum output tokens")

        repository = AIRegistryRepository(self.database_path)
        try:
            if repository.get_model_by_key(key):
                raise ValueError("This AI model key already exists.")
            created = repository.create_model(
                model_key=key,
                provider_code=provider,
                model_name=name,
                display_name=label,
                deployment_type=_PROVIDER_TYPES[provider],
                supports_structured_output=True,
                input_cost_per_million_usd=input_cost,
                output_cost_per_million_usd=output_cost,
                context_window=context_limit,
                max_output_tokens=output_limit,
                status=status_value,
                created_by_user_id=context.user_id,
            )
        except Exception:
            raise
        finally:
            repository.close()
        self._audit(
            context,
            action="AI_MODEL_REGISTERED",
            target_type="ai_model",
            target_id=str(created["id"]),
            details={
                "model_key": key,
                "provider_code": provider,
                "deployment_type": _PROVIDER_TYPES[provider],
                "status": status_value,
            },
        )
        return created

    def set_model_status(
        self,
        context: SecurityContext,
        *,
        model_id: int,
        status: str,
    ) -> dict[str, Any]:
        self._require_registry_management(context)
        status_value = str(status or "").strip().upper()
        if status_value not in _VALID_MODEL_STATUS:
            raise ValueError("Model status must be ACTIVE or INACTIVE.")
        repository = AIRegistryRepository(self.database_path)
        try:
            updated = repository.update_model_status(
                model_id=int(model_id),
                status=status_value,
            )
        finally:
            repository.close()
        self._audit(
            context,
            action="AI_MODEL_STATUS_CHANGED",
            target_type="ai_model",
            target_id=str(model_id),
            details={"model_key": updated["model_key"], "status": status_value},
        )
        return updated

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------

    def list_prompt_versions(
        self,
        context: SecurityContext,
        *,
        active_only: bool = False,
    ) -> list[dict[str, Any]]:
        AuthorizationService.require_permission(context, PERMISSION_AI_POLICY_VIEW)
        repository = AIRegistryRepository(self.database_path)
        try:
            records = repository.list_prompt_versions(active_only=active_only)
        finally:
            repository.close()
        if AuthorizationService.has_permission(
            context,
            PERMISSION_AI_POLICY_MANAGE_GLOBAL,
        ):
            return records
        return [_prompt_metadata(record) for record in records]

    def create_prompt_version(
        self,
        context: SecurityContext,
        *,
        prompt_key: str,
        task_code: str,
        system_template: str,
        user_template: str,
        output_schema: dict[str, Any] | str,
        activate: bool = False,
    ) -> dict[str, Any]:
        self._require_registry_management(context)
        key = str(prompt_key or "").strip().casefold()
        task = self.normalize_task_code(task_code)
        system = str(system_template or "").strip()
        user = str(user_template or "").strip()
        if not _KEY_PATTERN.fullmatch(key):
            raise ValueError(
                "Prompt key must start with a lowercase letter and contain only "
                "lowercase letters, numbers, dots, hyphens, or underscores."
            )
        if not user:
            raise ValueError("The user prompt template is required.")
        if len(system) > 20_000 or len(user) > 50_000:
            raise ValueError("The prompt template exceeds the RecruitOS size limit.")
        schema = _schema_object(output_schema)
        validate_schema_definition(schema)

        repository = AIRegistryRepository(self.database_path)
        try:
            version_number = repository.next_prompt_version(key)
            created = repository.create_prompt_version(
                prompt_key=key,
                task_code=task,
                version_number=version_number,
                system_template=system,
                user_template=user,
                output_schema=schema,
                status="DRAFT",
                created_by_user_id=context.user_id,
            )
            if activate:
                created = repository.activate_prompt_version(
                    prompt_version_id=int(created["id"]),
                    activated_by_user_id=context.user_id,
                )
        finally:
            repository.close()
        self._audit(
            context,
            action="AI_PROMPT_VERSION_CREATED",
            target_type="ai_prompt_version",
            target_id=str(created["id"]),
            details={
                "prompt_key": key,
                "task_code": task,
                "version_number": version_number,
                "activated": bool(activate),
                "schema_sha256": _schema_fingerprint(schema),
            },
        )
        return created

    def activate_prompt_version(
        self,
        context: SecurityContext,
        *,
        prompt_version_id: int,
    ) -> dict[str, Any]:
        self._require_registry_management(context)
        repository = AIRegistryRepository(self.database_path)
        try:
            activated = repository.activate_prompt_version(
                prompt_version_id=int(prompt_version_id),
                activated_by_user_id=context.user_id,
            )
        finally:
            repository.close()
        self._audit(
            context,
            action="AI_PROMPT_VERSION_ACTIVATED",
            target_type="ai_prompt_version",
            target_id=str(prompt_version_id),
            details={
                "prompt_key": activated["prompt_key"],
                "task_code": activated["task_code"],
                "version_number": activated["version_number"],
            },
        )
        return activated

    # ------------------------------------------------------------------
    # Tenant/user policy
    # ------------------------------------------------------------------

    def get_policy(
        self,
        context: SecurityContext,
        *,
        task_code: str,
        target_user_id: int | None = None,
    ) -> dict[str, Any] | None:
        target = self._target_user(
            context,
            target_user_id or context.user_id,
            manage=False,
        )
        repository = AIRegistryRepository(self.database_path)
        try:
            policy = repository.get_policy(
                tenant_id=int(target["tenant_id"]),
                target_user_id=int(target["id"]),
                task_code=self.normalize_task_code(task_code),
            )
        finally:
            repository.close()
        return _policy_metadata(policy) if policy else None

    def list_policies(
        self,
        context: SecurityContext,
        *,
        target_user_id: int | None = None,
    ) -> list[dict[str, Any]]:
        target = self._target_user(
            context,
            target_user_id or context.user_id,
            manage=False,
        )
        repository = AIRegistryRepository(self.database_path)
        try:
            return repository.list_policies(
                tenant_id=int(target["tenant_id"]),
                target_user_id=int(target["id"]),
            )
        finally:
            repository.close()

    def set_policy(
        self,
        context: SecurityContext,
        *,
        target_user_id: int,
        task_code: str,
        model_id: int,
        prompt_version_id: int,
        enabled: bool = False,
        allow_external_data: bool = False,
        max_input_chars: int = AI_DEFAULT_MAX_INPUT_CHARS,
        timeout_seconds: int = AI_HTTP_TIMEOUT_SECONDS,
        daily_request_limit: int = AI_DEFAULT_DAILY_REQUEST_LIMIT,
    ) -> dict[str, Any]:
        target = self._target_user(context, target_user_id, manage=True)
        task = self.normalize_task_code(task_code)
        input_limit = max(1_000, min(int(max_input_chars), 2_000_000))
        timeout = max(5, min(int(timeout_seconds), 600))
        daily_limit = max(1, min(int(daily_request_limit), 100_000))

        repository = AIRegistryRepository(self.database_path)
        try:
            model = repository.get_model(int(model_id))
            prompt = repository.get_prompt_version(int(prompt_version_id))
            if not model or str(model.get("status")) != "ACTIVE":
                raise ValueError("Select an active AI model.")
            if not bool(model.get("supports_structured_output")):
                raise ValueError("The selected model does not support structured output.")
            if not prompt or str(prompt.get("status")) != "ACTIVE":
                raise ValueError("Select an active AI prompt version.")
            if str(prompt.get("task_code")) != task:
                raise ValueError("The selected prompt version belongs to a different AI task.")
            policy = repository.upsert_policy(
                tenant_id=int(target["tenant_id"]),
                target_user_id=int(target["id"]),
                task_code=task,
                enabled=bool(enabled),
                model_id=int(model_id),
                prompt_version_id=int(prompt_version_id),
                allow_external_data=bool(allow_external_data),
                max_input_chars=input_limit,
                timeout_seconds=timeout,
                daily_request_limit=daily_limit,
                created_by_user_id=context.user_id,
            )
        finally:
            repository.close()
        self._audit(
            context,
            action="AI_TENANT_POLICY_UPDATED",
            target_type="tenant_ai_policy",
            target_id=str(policy["id"]),
            details={
                "target_user_id": int(target["id"]),
                "target_tenant_id": int(target["tenant_id"]),
                "task_code": task,
                "model_key": policy["model_key"],
                "prompt_key": policy["prompt_key"],
                "prompt_version_number": policy["prompt_version_number"],
                "enabled": bool(enabled),
                "allow_external_data": bool(allow_external_data),
                "max_input_chars": input_limit,
                "timeout_seconds": timeout,
                "daily_request_limit": daily_limit,
            },
        )
        return policy

    # ------------------------------------------------------------------
    # Telemetry
    # ------------------------------------------------------------------

    def telemetry(
        self,
        context: SecurityContext,
        *,
        target_user_id: int | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        target = self._target_user(
            context,
            target_user_id or context.user_id,
            manage=False,
        )
        repository = AIRegistryRepository(self.database_path)
        try:
            return {
                "summary": repository.telemetry_summary(
                    tenant_id=int(target["tenant_id"]),
                    user_id=int(target["id"]),
                ),
                "events": repository.list_inference_events(
                    tenant_id=int(target["tenant_id"]),
                    user_id=int(target["id"]),
                    limit=limit,
                ),
            }
        finally:
            repository.close()

    # ------------------------------------------------------------------
    # Authorization and audit
    # ------------------------------------------------------------------

    def _require_registry_management(self, context: SecurityContext) -> None:
        if not AuthorizationService.has_permission(
            context,
            PERMISSION_AI_POLICY_MANAGE_GLOBAL,
        ):
            raise PermissionError(
                "Only the System Owner or Global Admin can manage AI models and prompts."
            )

    def _target_user(
        self,
        context: SecurityContext,
        target_user_id: int,
        *,
        manage: bool,
    ) -> dict[str, Any]:
        context.require_valid()
        AuthorizationService.require_permission(context, PERMISSION_AI_POLICY_VIEW)
        users = UserRepository(self.database_path)
        try:
            target = users.get_user_by_id(int(target_user_id))
        finally:
            users.close()
        if not target:
            raise LookupError("The selected RecruitOS user was not found.")
        if int(target["id"]) == context.user_id:
            if manage and not (
                AuthorizationService.has_permission(
                    context,
                    PERMISSION_AI_POLICY_MANAGE_GLOBAL,
                )
                or AuthorizationService.has_permission(
                    context,
                    PERMISSION_AI_POLICY_MANAGE_TENANT,
                )
            ):
                raise PermissionError("This role cannot manage AI policy.")
            return target

        if not manage:
            manage = True
        if manage and not (
            AuthorizationService.has_permission(
                context,
                PERMISSION_AI_POLICY_MANAGE_GLOBAL,
            )
            or AuthorizationService.has_permission(
                context,
                PERMISSION_AI_POLICY_MANAGE_TENANT,
            )
        ):
            raise PermissionError("This role cannot manage another workspace's AI policy.")
        decision = AuthorizationService.can_manage_target(
            context,
            target_role=str(target.get("role_code") or "USER"),
            target_country_location=str(target.get("country_location") or ""),
        )
        if not decision.allowed:
            raise PermissionError(decision.reason)
        return target

    def _audit(
        self,
        context: SecurityContext,
        *,
        action: str,
        target_type: str,
        target_id: str,
        details: dict[str, Any],
    ) -> None:
        repository = UserRepository(self.database_path)
        try:
            repository.audit_event(
                tenant_id=context.tenant_id,
                actor_user_id=context.user_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                details=details,
            )
        finally:
            repository.close()

    @staticmethod
    def normalize_task_code(task_code: str) -> str:
        value = str(task_code or "").strip().upper().replace(" ", "_")
        if not _CODE_PATTERN.fullmatch(value):
            raise ValueError(
                "AI task code must start with a letter and contain only uppercase "
                "letters, numbers, or underscores."
            )
        return value


def _schema_object(value: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    try:
        parsed = json.loads(str(value or ""))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Output schema is not valid JSON at line {exc.lineno}, column {exc.colno}."
        ) from exc
    if not isinstance(parsed, dict):
        raise ValueError("Output schema must be a JSON object.")
    return parsed


def _schema_fingerprint(schema: dict[str, Any]) -> str:
    from hashlib import sha256

    encoded = json.dumps(
        schema,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _non_negative_float(value: Any, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric.") from exc
    if number < 0:
        raise ValueError(f"{label} cannot be negative.")
    return number


def _non_negative_int(value: Any, label: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a whole number.") from exc
    if number < 0:
        raise ValueError(f"{label} cannot be negative.")
    return number


def _safe_endpoint_label(raw_url: str) -> str:
    from urllib.parse import urlsplit

    try:
        parsed = urlsplit(str(raw_url or ""))
    except ValueError:
        return "Invalid endpoint"
    if not parsed.scheme or not parsed.netloc:
        return "Not configured"
    return f"{parsed.scheme}://{parsed.netloc}"


def _prompt_metadata(record: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in record.items()
        if key not in {
            "system_template",
            "user_template",
            "output_schema",
            "output_schema_json",
        }
    }


def _policy_metadata(record: dict[str, Any]) -> dict[str, Any]:
    return _prompt_metadata(record)
