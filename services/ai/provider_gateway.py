"""Policy-enforced RecruitOS AI provider gateway with safe telemetry."""
from __future__ import annotations

import json
import re
from pathlib import Path
from string import Template
from time import perf_counter
from typing import Any, Mapping
from uuid import uuid4

from database.ai_registry_repository import AIRegistryRepository
from models.ai_contracts import (
    AIGatewayResponse,
    AIModelDefinition,
    AIProviderRequest,
    AIProviderResponse,
    AIPromptVersion,
)
from models.security_context import SecurityContext
from services.ai.errors import (
    AIConfigurationError,
    AIError,
    AIPolicyError,
)
from services.ai.providers import (
    AIProvider,
    OllamaProvider,
    OpenAIResponsesProvider,
)
from services.ai.schema_validator import validate_structured_output
from services.ai_registry_service import AIRegistryService
from services.authorization_service import (
    PERMISSION_AI_INFERENCE_RUN,
    AuthorizationService,
)


class AIProviderGateway:
    """Execute one explicitly enabled structured task without persisting content."""

    def __init__(
        self,
        database_path: str | Path | None = None,
        *,
        providers: Mapping[str, AIProvider] | None = None,
    ) -> None:
        self.database_path = database_path
        self.registry_service = AIRegistryService(database_path)
        self.providers: dict[str, AIProvider] = {
            "OPENAI": OpenAIResponsesProvider(),
            "OLLAMA": OllamaProvider(),
            **{str(key).upper(): value for key, value in dict(providers or {}).items()},
        }

    def generate_structured(
        self,
        context: SecurityContext,
        *,
        task_code: str,
        variables: Mapping[str, Any],
    ) -> AIGatewayResponse:
        context.require_valid()
        AuthorizationService.require_permission(context, PERMISSION_AI_INFERENCE_RUN)
        task = AIRegistryService.normalize_task_code(task_code)
        request_id = uuid4().hex
        started = perf_counter()
        repository = AIRegistryRepository(self.database_path)
        policy: dict[str, Any] | None = None
        input_chars = 0
        provider_code = ""
        model_key = ""
        model_id: int | None = None
        prompt_version_id: int | None = None

        try:
            policy = repository.get_policy(
                tenant_id=context.tenant_id,
                target_user_id=context.user_id,
                task_code=task,
            )
            if not policy:
                raise AIPolicyError(
                    f"No AI policy is assigned for task {task}."
                )
            provider_code = str(policy["provider_code"])
            model_key = str(policy["model_key"])
            model_id = int(policy["model_id"])
            prompt_version_id = int(policy["prompt_version_id"])
            self._validate_policy(policy)

            used_today = repository.count_requests_today(
                tenant_id=context.tenant_id,
                user_id=context.user_id,
                task_code=task,
            )
            if used_today >= int(policy["daily_request_limit"]):
                raise AIPolicyError(
                    "The daily AI request limit for this task has been reached."
                )

            system_prompt, user_prompt = self._render_prompt(policy, variables)
            input_chars = len(system_prompt) + len(user_prompt)
            if input_chars > int(policy["max_input_chars"]):
                raise AIPolicyError(
                    "The AI task input exceeds the configured character limit."
                )

            model = AIModelDefinition.from_record(
                {
                    "id": policy["model_id"],
                    "model_key": policy["model_key"],
                    "provider_code": policy["provider_code"],
                    "model_name": policy["model_name"],
                    "display_name": policy["display_name"],
                    "deployment_type": policy["deployment_type"],
                    "supports_structured_output": policy["supports_structured_output"],
                    "input_cost_per_million_usd": policy["input_cost_per_million_usd"],
                    "output_cost_per_million_usd": policy["output_cost_per_million_usd"],
                    "context_window": policy["context_window"],
                    "max_output_tokens": policy["max_output_tokens"],
                    "status": policy["model_status"],
                }
            )
            prompt = AIPromptVersion.from_record(
                {
                    "id": policy["prompt_version_id"],
                    "prompt_key": policy["prompt_key"],
                    "task_code": policy["task_code"],
                    "version_number": policy["prompt_version_number"],
                    "system_template": policy["system_template"],
                    "user_template": policy["user_template"],
                    "output_schema": policy["output_schema"],
                    "status": policy["prompt_status"],
                }
            )
            provider = self.providers.get(provider_code)
            if not provider:
                raise AIConfigurationError(
                    f"No provider adapter is registered for {provider_code}."
                )
            if model.deployment_type == "HOSTED" and not bool(
                policy["allow_external_data"]
            ):
                raise AIPolicyError(
                    "Hosted AI data transfer is disabled for this workspace policy."
                )

            provider_response = provider.generate_structured(
                AIProviderRequest(
                    request_id=request_id,
                    task_code=task,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    output_schema=prompt.output_schema,
                    max_output_tokens=model.max_output_tokens,
                    timeout_seconds=int(policy["timeout_seconds"]),
                ),
                model,
            )
            validate_structured_output(provider_response.payload, prompt.output_schema)
            latency_ms = max(0, int(round((perf_counter() - started) * 1000)))
            cost = self._estimated_cost(model, provider_response)
            output_chars = len(
                json.dumps(provider_response.payload, ensure_ascii=False)
            )
            repository.record_inference_event(
                tenant_id=context.tenant_id,
                user_id=context.user_id,
                task_code=task,
                provider_code=provider_code,
                model_id=model.id,
                model_key=model.model_key,
                prompt_version_id=prompt.id,
                request_id=request_id,
                outcome="SUCCESS",
                latency_ms=latency_ms,
                input_chars=input_chars,
                output_chars=output_chars,
                input_tokens=provider_response.input_tokens,
                output_tokens=provider_response.output_tokens,
                estimated_cost_usd=cost,
            )
            return AIGatewayResponse(
                request_id=request_id,
                task_code=task,
                provider_code=provider_code,
                model_key=model.model_key,
                prompt_key=prompt.prompt_key,
                prompt_version=prompt.version_number,
                payload=dict(provider_response.payload),
                latency_ms=latency_ms,
                input_tokens=provider_response.input_tokens,
                output_tokens=provider_response.output_tokens,
                estimated_cost_usd=cost,
            )
        except Exception as exc:
            latency_ms = max(0, int(round((perf_counter() - started) * 1000)))
            error_code = getattr(exc, "error_code", exc.__class__.__name__.upper())
            outcome = "DENIED" if isinstance(exc, (AIPolicyError, PermissionError)) else "ERROR"
            repository.record_inference_event(
                tenant_id=context.tenant_id,
                user_id=context.user_id,
                task_code=task,
                provider_code=provider_code,
                model_id=model_id,
                model_key=model_key,
                prompt_version_id=prompt_version_id,
                request_id=request_id,
                outcome=outcome,
                latency_ms=latency_ms,
                input_chars=input_chars,
                output_chars=0,
                input_tokens=0,
                output_tokens=0,
                estimated_cost_usd=0.0,
                error_code=str(error_code),
                error_message_redacted=self._redacted_error(exc),
            )
            raise
        finally:
            repository.close()

    @staticmethod
    def _validate_policy(policy: Mapping[str, Any]) -> None:
        if not bool(policy.get("enabled")):
            raise AIPolicyError("This AI task is disabled for the current workspace.")
        if str(policy.get("model_status")) != "ACTIVE":
            raise AIPolicyError("The AI model assigned to this task is inactive.")
        if str(policy.get("prompt_status")) != "ACTIVE":
            raise AIPolicyError("The AI prompt assigned to this task is inactive.")
        if not bool(policy.get("supports_structured_output")):
            raise AIPolicyError("The assigned model does not support structured output.")

    @staticmethod
    def _render_prompt(
        policy: Mapping[str, Any],
        variables: Mapping[str, Any],
    ) -> tuple[str, str]:
        values = {
            str(key): _prompt_value(value)
            for key, value in dict(variables or {}).items()
        }
        try:
            system = Template(str(policy.get("system_template") or "")).substitute(values)
            user = Template(str(policy.get("user_template") or "")).substitute(values)
        except KeyError as exc:
            raise AIPolicyError(
                f"Prompt variable {exc.args[0]!r} was not supplied."
            ) from exc
        return system.strip(), user.strip()

    @staticmethod
    def _estimated_cost(
        model: AIModelDefinition,
        response: AIProviderResponse,
    ) -> float:
        input_cost = (
            max(0, int(response.input_tokens))
            * max(0.0, model.input_cost_per_million_usd)
            / 1_000_000
        )
        output_cost = (
            max(0, int(response.output_tokens))
            * max(0.0, model.output_cost_per_million_usd)
            / 1_000_000
        )
        return round(input_cost + output_cost, 8)

    @staticmethod
    def _redacted_error(exc: Exception) -> str:
        message = str(exc or "AI request failed.")
        message = re.sub(
            r"(?i)(bearer\s+)[A-Za-z0-9._~+\-/=]+",
            r"\1<redacted>",
            message,
        )
        message = re.sub(
            r"(?i)(api[_ -]?key\s*[:=]\s*)\S+",
            r"\1<redacted>",
            message,
        )
        return message.replace("\n", " ")[:240]


def _prompt_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
