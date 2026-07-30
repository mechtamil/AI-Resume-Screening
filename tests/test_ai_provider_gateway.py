"""Policy enforcement, validation, telemetry, and secret-redaction tests."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from models.ai_contracts import AIProviderResponse
from services.ai.errors import AIPolicyError, AIStructuredOutputError
from services.ai.provider_gateway import AIProviderGateway
from services.ai.providers.base import AIProvider
from services.ai_registry_service import AIRegistryService
from services.authorization_service import USER
from tests.security_test_utils import create_context, create_owner_context


SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string", "minLength": 1},
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
    },
    "required": ["summary", "score"],
    "additionalProperties": False,
}


class FakeProvider(AIProvider):
    provider_code = "OLLAMA"
    deployment_type = "LOCAL"

    def __init__(self, payload=None, *, input_tokens=100, output_tokens=20) -> None:
        self.payload = payload or {"summary": "Structured evidence", "score": 91}
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.calls = []

    def generate_structured(self, request, model):
        self.calls.append((request, model))
        return AIProviderResponse(
            payload=self.payload,
            provider_request_id="fake-provider-request",
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
        )


class AIProviderGatewayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp.name) / "recruitos.db"
        self.owner = create_owner_context(self.database_path)
        self.user = create_context(
            self.database_path,
            "gateway.user@example.com",
            "Gateway User",
            user_id="GATEWAY-USER",
            role=USER,
        )
        self.registry = AIRegistryService(self.database_path)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _assets(self, *, provider="OLLAMA", input_cost=2.0, output_cost=8.0):
        model = self.registry.register_model(
            self.owner,
            model_key=f"{provider.casefold()}.gateway-test",
            provider_code=provider,
            model_name="gateway-test-model",
            display_name="Gateway Test Model",
            input_cost_per_million_usd=input_cost,
            output_cost_per_million_usd=output_cost,
            context_window=32000,
            max_output_tokens=1000,
        )
        prompt = self.registry.create_prompt_version(
            self.owner,
            prompt_key=f"test.{provider.casefold()}-gateway",
            task_code="TEST_TASK",
            system_template="Use only the supplied content.",
            user_template="Document: $document_text",
            output_schema=SCHEMA,
            activate=True,
        )
        return model, prompt

    def _policy(self, model, prompt, **overrides):
        values = {
            "enabled": True,
            "allow_external_data": False,
            "max_input_chars": 10_000,
            "timeout_seconds": 30,
            "daily_request_limit": 10,
            **overrides,
        }
        return self.registry.set_policy(
            self.owner,
            target_user_id=self.user.user_id,
            task_code="TEST_TASK",
            model_id=model["id"],
            prompt_version_id=prompt["id"],
            **values,
        )

    def test_local_policy_executes_validated_structured_output_and_cost(self) -> None:
        model, prompt = self._assets()
        self._policy(model, prompt)
        provider = FakeProvider(input_tokens=1000, output_tokens=500)
        gateway = AIProviderGateway(
            self.database_path,
            providers={"OLLAMA": provider},
        )
        response = gateway.generate_structured(
            self.user,
            task_code="TEST_TASK",
            variables={"document_text": "Synthetic candidate data"},
        )

        self.assertEqual(response.payload["score"], 91)
        self.assertEqual(response.model_key, "ollama.gateway-test")
        self.assertAlmostEqual(response.estimated_cost_usd, 0.006, places=8)
        self.assertEqual(len(provider.calls), 1)

        telemetry = self.registry.telemetry(self.user)
        self.assertEqual(telemetry["summary"]["total_requests"], 1)
        self.assertEqual(telemetry["summary"]["successes"], 1)
        event = telemetry["events"][0]
        self.assertEqual(event["outcome"], "SUCCESS")
        self.assertNotIn("Synthetic candidate data", str(event))
        self.assertNotIn("Structured evidence", str(event))

    def test_disabled_policy_is_denied_and_provider_is_not_called(self) -> None:
        model, prompt = self._assets()
        self._policy(model, prompt, enabled=False)
        provider = FakeProvider()
        gateway = AIProviderGateway(
            self.database_path,
            providers={"OLLAMA": provider},
        )
        with self.assertRaisesRegex(AIPolicyError, "disabled"):
            gateway.generate_structured(
                self.user,
                task_code="TEST_TASK",
                variables={"document_text": "Synthetic"},
            )
        self.assertEqual(provider.calls, [])
        event = self.registry.telemetry(self.user)["events"][0]
        self.assertEqual(event["outcome"], "DENIED")

    def test_hosted_provider_requires_explicit_external_transfer(self) -> None:
        model, prompt = self._assets(provider="OPENAI")
        self._policy(model, prompt, allow_external_data=False)
        provider = FakeProvider()
        provider.provider_code = "OPENAI"
        provider.deployment_type = "HOSTED"
        gateway = AIProviderGateway(
            self.database_path,
            providers={"OPENAI": provider},
        )
        with self.assertRaisesRegex(AIPolicyError, "data transfer is disabled"):
            gateway.generate_structured(
                self.user,
                task_code="TEST_TASK",
                variables={"document_text": "Synthetic"},
            )
        self.assertEqual(provider.calls, [])

    def test_invalid_structured_output_is_rejected_and_logged_without_content(self) -> None:
        model, prompt = self._assets()
        self._policy(model, prompt)
        provider = FakeProvider(payload={"summary": "Missing score"})
        gateway = AIProviderGateway(
            self.database_path,
            providers={"OLLAMA": provider},
        )
        with self.assertRaises(AIStructuredOutputError):
            gateway.generate_structured(
                self.user,
                task_code="TEST_TASK",
                variables={"document_text": "Confidential synthetic text"},
            )
        event = self.registry.telemetry(self.user)["events"][0]
        self.assertEqual(event["outcome"], "ERROR")
        self.assertEqual(event["error_code"], "AI_STRUCTURED_OUTPUT_ERROR")
        self.assertNotIn("Confidential synthetic text", str(event))
        self.assertNotIn("Missing score", str(event))

    def test_missing_prompt_variable_is_denied_before_provider_call(self) -> None:
        model, prompt = self._assets()
        self._policy(model, prompt)
        provider = FakeProvider()
        gateway = AIProviderGateway(
            self.database_path,
            providers={"OLLAMA": provider},
        )
        with self.assertRaisesRegex(AIPolicyError, "document_text"):
            gateway.generate_structured(
                self.user,
                task_code="TEST_TASK",
                variables={},
            )
        self.assertEqual(provider.calls, [])

    def test_daily_limit_is_enforced(self) -> None:
        model, prompt = self._assets()
        self._policy(model, prompt, daily_request_limit=1)
        provider = FakeProvider()
        gateway = AIProviderGateway(
            self.database_path,
            providers={"OLLAMA": provider},
        )
        gateway.generate_structured(
            self.user,
            task_code="TEST_TASK",
            variables={"document_text": "First"},
        )
        with self.assertRaisesRegex(AIPolicyError, "daily AI request limit"):
            gateway.generate_structured(
                self.user,
                task_code="TEST_TASK",
                variables={"document_text": "Second"},
            )
        self.assertEqual(len(provider.calls), 1)

    def test_error_redaction_removes_bearer_and_api_key_values(self) -> None:
        message = AIProviderGateway._redacted_error(
            RuntimeError("Bearer secret-token api_key=top-secret")
        )
        self.assertNotIn("secret-token", message)
        self.assertNotIn("top-secret", message)
        self.assertIn("<redacted>", message)


if __name__ == "__main__":
    unittest.main()
