"""Ollama local-provider adapter using its structured chat endpoint."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from config.settings import AI_MAX_RESPONSE_BYTES, AI_OLLAMA_BASE_URL
from models.ai_contracts import AIModelDefinition, AIProviderRequest, AIProviderResponse
from services.ai.errors import AIConfigurationError, AIProviderError
from services.ai.providers.base import AIProvider, JsonTransport, post_json
from services.ai.schema_validator import parse_json_response


class OllamaProvider(AIProvider):
    provider_code = "OLLAMA"
    deployment_type = "LOCAL"

    def __init__(
        self,
        *,
        base_url: str = AI_OLLAMA_BASE_URL,
        transport: JsonTransport = post_json,
        max_response_bytes: int = AI_MAX_RESPONSE_BYTES,
    ) -> None:
        self.base_url = str(base_url or "").strip().rstrip("/")
        self.transport = transport
        self.max_response_bytes = int(max_response_bytes)

    def generate_structured(
        self,
        request: AIProviderRequest,
        model: AIModelDefinition,
    ) -> AIProviderResponse:
        if not self.base_url:
            raise AIConfigurationError(
                "Ollama is not configured. Set RECRUITOS_OLLAMA_BASE_URL."
            )
        payload: dict[str, Any] = {
            "model": model.model_name,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
            "format": dict(request.output_schema),
            "stream": False,
            "think": False,
        }
        if request.max_output_tokens > 0:
            payload["options"] = {"num_predict": int(request.max_output_tokens)}

        envelope = self.transport(
            f"{self.base_url}/api/chat",
            {},
            payload,
            request.timeout_seconds,
            self.max_response_bytes,
        )
        message = envelope.get("message")
        if not isinstance(message, Mapping):
            raise AIProviderError("Ollama response did not contain a message object.")
        content = message.get("content")
        parsed = parse_json_response(str(content or ""))
        if not isinstance(parsed, Mapping):
            raise AIProviderError("Ollama structured output must be a JSON object.")
        return AIProviderResponse(
            payload=dict(parsed),
            provider_request_id=str(envelope.get("created_at") or ""),
            input_tokens=int(envelope.get("prompt_eval_count") or 0),
            output_tokens=int(envelope.get("eval_count") or 0),
            raw_metadata={
                "done_reason": str(envelope.get("done_reason") or ""),
                "total_duration_ns": int(envelope.get("total_duration") or 0),
            },
        )
