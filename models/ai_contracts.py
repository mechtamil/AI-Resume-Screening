"""Immutable contracts for RecruitOS AI provider calls and registry records."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class AIModelDefinition:
    """Public model metadata. Secret provider credentials are never stored here."""

    id: int
    model_key: str
    provider_code: str
    model_name: str
    display_name: str
    deployment_type: str
    supports_structured_output: bool
    input_cost_per_million_usd: float = 0.0
    output_cost_per_million_usd: float = 0.0
    context_window: int = 0
    max_output_tokens: int = 0
    status: str = "ACTIVE"

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "AIModelDefinition":
        return cls(
            id=int(record["id"]),
            model_key=str(record["model_key"]),
            provider_code=str(record["provider_code"]),
            model_name=str(record["model_name"]),
            display_name=str(record.get("display_name") or record["model_name"]),
            deployment_type=str(record["deployment_type"]),
            supports_structured_output=bool(record.get("supports_structured_output", 0)),
            input_cost_per_million_usd=float(
                record.get("input_cost_per_million_usd") or 0.0
            ),
            output_cost_per_million_usd=float(
                record.get("output_cost_per_million_usd") or 0.0
            ),
            context_window=int(record.get("context_window") or 0),
            max_output_tokens=int(record.get("max_output_tokens") or 0),
            status=str(record.get("status") or "ACTIVE"),
        )


@dataclass(frozen=True, slots=True)
class AIPromptVersion:
    """One immutable prompt and structured-output schema version."""

    id: int
    prompt_key: str
    task_code: str
    version_number: int
    system_template: str
    user_template: str
    output_schema: Mapping[str, Any]
    status: str = "ACTIVE"

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "AIPromptVersion":
        return cls(
            id=int(record["id"]),
            prompt_key=str(record["prompt_key"]),
            task_code=str(record["task_code"]),
            version_number=int(record["version_number"]),
            system_template=str(record.get("system_template") or ""),
            user_template=str(record.get("user_template") or ""),
            output_schema=dict(record.get("output_schema") or {}),
            status=str(record.get("status") or "ACTIVE"),
        )


@dataclass(frozen=True, slots=True)
class AITenantPolicy:
    """Effective tenant/user policy for one AI task."""

    id: int
    tenant_id: int
    target_user_id: int
    task_code: str
    enabled: bool
    model_id: int
    prompt_version_id: int
    allow_external_data: bool
    max_input_chars: int
    timeout_seconds: int
    daily_request_limit: int

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "AITenantPolicy":
        return cls(
            id=int(record["id"]),
            tenant_id=int(record["tenant_id"]),
            target_user_id=int(record["target_user_id"]),
            task_code=str(record["task_code"]),
            enabled=bool(record.get("enabled", 0)),
            model_id=int(record["model_id"]),
            prompt_version_id=int(record["prompt_version_id"]),
            allow_external_data=bool(record.get("allow_external_data", 0)),
            max_input_chars=int(record.get("max_input_chars") or 0),
            timeout_seconds=int(record.get("timeout_seconds") or 0),
            daily_request_limit=int(record.get("daily_request_limit") or 0),
        )


@dataclass(frozen=True, slots=True)
class AIProviderRequest:
    """Provider-neutral request assembled after policy and prompt resolution."""

    request_id: str
    task_code: str
    system_prompt: str
    user_prompt: str
    output_schema: Mapping[str, Any]
    max_output_tokens: int
    timeout_seconds: int


@dataclass(frozen=True, slots=True)
class AIProviderResponse:
    """Provider-neutral structured result and usage metadata."""

    payload: Mapping[str, Any]
    provider_request_id: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    raw_metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AIGatewayResponse:
    """Validated response returned to an authorized RecruitOS caller."""

    request_id: str
    task_code: str
    provider_code: str
    model_key: str
    prompt_key: str
    prompt_version: int
    payload: Mapping[str, Any]
    latency_ms: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
