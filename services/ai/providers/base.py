"""Provider protocol and secret-safe JSON HTTP transport."""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from models.ai_contracts import AIModelDefinition, AIProviderRequest, AIProviderResponse
from services.ai.errors import AIProviderError

JsonTransport = Callable[[str, Mapping[str, str], Mapping[str, Any], int, int], Mapping[str, Any]]


@dataclass(frozen=True, slots=True)
class ProviderRuntime:
    """Deployment-only provider configuration; repr never includes a credential."""

    provider_code: str
    base_url: str
    configured: bool
    api_key: str = ""

    def __repr__(self) -> str:
        return (
            "ProviderRuntime(provider_code={!r}, base_url={!r}, configured={!r}, "
            "api_key=<redacted>)"
        ).format(self.provider_code, self.base_url, self.configured)


class AIProvider(ABC):
    """Provider-neutral structured-generation interface."""

    provider_code: str
    deployment_type: str

    @abstractmethod
    def generate_structured(
        self,
        request: AIProviderRequest,
        model: AIModelDefinition,
    ) -> AIProviderResponse:
        raise NotImplementedError


def post_json(
    url: str,
    headers: Mapping[str, str],
    payload: Mapping[str, Any],
    timeout_seconds: int,
    max_response_bytes: int,
) -> Mapping[str, Any]:
    """POST JSON with a strict response-size ceiling and sanitized errors."""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        str(url),
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            **dict(headers),
        },
    )
    try:
        with urlopen(request, timeout=max(1, int(timeout_seconds))) as response:
            raw = response.read(max(1024, int(max_response_bytes)) + 1)
    except HTTPError as exc:
        message = f"AI provider returned HTTP {exc.code}."
        raise AIProviderError(message) from exc
    except URLError as exc:
        raise AIProviderError("AI provider could not be reached.") from exc
    except TimeoutError as exc:
        raise AIProviderError("AI provider request timed out.") from exc

    if len(raw) > int(max_response_bytes):
        raise AIProviderError("AI provider response exceeded the configured size limit.")
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AIProviderError("AI provider returned an invalid JSON envelope.") from exc
    if not isinstance(parsed, Mapping):
        raise AIProviderError("AI provider returned an unsupported response envelope.")
    return parsed
