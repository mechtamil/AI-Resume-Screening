"""OpenAI Responses API adapter with strict JSON-schema output and no storage."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from config.settings import (
    AI_MAX_RESPONSE_BYTES,
    AI_OPENAI_API_KEY,
    AI_OPENAI_BASE_URL,
)
from models.ai_contracts import AIModelDefinition, AIProviderRequest, AIProviderResponse
from services.ai.errors import AIConfigurationError, AIProviderError
from services.ai.providers.base import AIProvider, JsonTransport, post_json
from services.ai.schema_validator import parse_json_response


class OpenAIResponsesProvider(AIProvider):
    provider_code = "OPENAI"
    deployment_type = "HOSTED"

    def __init__(
        self,
        *,
        base_url: str = AI_OPENAI_BASE_URL,
        api_key: str = AI_OPENAI_API_KEY,
        transport: JsonTransport = post_json,
        max_response_bytes: int = AI_MAX_RESPONSE_BYTES,
    ) -> None:
        self.base_url = str(base_url or "").strip().rstrip("/")
        self.api_key = str(api_key or "").strip()
        self.transport = transport
        self.max_response_bytes = int(max_response_bytes)

    def generate_structured(
        self,
        request: AIProviderRequest,
        model: AIModelDefinition,
    ) -> AIProviderResponse:
        if not self.base_url or not self.api_key:
            raise AIConfigurationError(
                "OpenAI is not configured. Set RECRUITOS_OPENAI_API_KEY and "
                "RECRUITOS_OPENAI_BASE_URL in deployment secrets."
            )

        schema_name = _schema_name(request.task_code)
        payload: dict[str, Any] = {
            "model": model.model_name,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": request.system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": request.user_prompt}],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": dict(request.output_schema),
                    "strict": True,
                }
            },
            "store": False,
        }
        if request.max_output_tokens > 0:
            payload["max_output_tokens"] = int(request.max_output_tokens)

        envelope = self.transport(
            f"{self.base_url}/responses",
            {"Authorization": f"Bearer {self.api_key}"},
            payload,
            request.timeout_seconds,
            self.max_response_bytes,
        )
        text = _output_text(envelope)
        parsed = parse_json_response(text)
        if not isinstance(parsed, Mapping):
            raise AIProviderError("OpenAI structured output must be a JSON object.")
        usage = envelope.get("usage")
        if not isinstance(usage, Mapping):
            usage = {}
        return AIProviderResponse(
            payload=dict(parsed),
            provider_request_id=str(envelope.get("id") or ""),
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
            raw_metadata={"status": str(envelope.get("status") or "")},
        )


def _output_text(envelope: Mapping[str, Any]) -> str:
    direct = envelope.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct
    output = envelope.get("output")
    if not isinstance(output, Sequence) or isinstance(output, (str, bytes, bytearray)):
        raise AIProviderError("OpenAI response did not contain structured output text.")
    for item in output:
        if not isinstance(item, Mapping):
            continue
        content = item.get("content")
        if not isinstance(content, Sequence) or isinstance(content, (str, bytes, bytearray)):
            continue
        for part in content:
            if not isinstance(part, Mapping):
                continue
            if part.get("type") == "output_text" and isinstance(part.get("text"), str):
                return str(part["text"])
    raise AIProviderError("OpenAI response did not contain structured output text.")


def _schema_name(task_code: str) -> str:
    value = "".join(
        character.lower() if character.isalnum() else "_"
        for character in str(task_code or "structured_output")
    ).strip("_")
    return (value or "structured_output")[:64]
