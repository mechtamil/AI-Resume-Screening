"""Provider-adapter request and response contract tests without network access."""
from __future__ import annotations

import unittest

from models.ai_contracts import AIModelDefinition, AIProviderRequest
from services.ai.errors import AIConfigurationError
from services.ai.providers.ollama import OllamaProvider
from services.ai.providers.openai_responses import OpenAIResponsesProvider


SCHEMA = {
    "type": "object",
    "properties": {"summary": {"type": "string"}},
    "required": ["summary"],
    "additionalProperties": False,
}


class AIProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.request = AIProviderRequest(
            request_id="request-1",
            task_code="TEST_TASK",
            system_prompt="System",
            user_prompt="User",
            output_schema=SCHEMA,
            max_output_tokens=500,
            timeout_seconds=30,
        )

    def test_ollama_adapter_uses_schema_and_usage_metadata(self) -> None:
        captured = {}

        def transport(url, headers, payload, timeout, max_bytes):
            captured.update(
                url=url,
                headers=headers,
                payload=payload,
                timeout=timeout,
                max_bytes=max_bytes,
            )
            return {
                "message": {"role": "assistant", "content": '{"summary":"ok"}'},
                "prompt_eval_count": 12,
                "eval_count": 6,
                "done_reason": "stop",
                "total_duration": 100,
            }

        provider = OllamaProvider(
            base_url="http://127.0.0.1:11434",
            transport=transport,
        )
        model = AIModelDefinition(
            id=1,
            model_key="ollama.test",
            provider_code="OLLAMA",
            model_name="test-model",
            display_name="Test Model",
            deployment_type="LOCAL",
            supports_structured_output=True,
            max_output_tokens=500,
        )
        result = provider.generate_structured(self.request, model)

        self.assertEqual(captured["url"], "http://127.0.0.1:11434/api/chat")
        self.assertEqual(captured["payload"]["format"], SCHEMA)
        self.assertFalse(captured["payload"]["stream"])
        self.assertEqual(result.payload, {"summary": "ok"})
        self.assertEqual(result.input_tokens, 12)
        self.assertEqual(result.output_tokens, 6)

    def test_openai_adapter_uses_responses_schema_and_store_false(self) -> None:
        captured = {}

        def transport(url, headers, payload, timeout, max_bytes):
            captured.update(
                url=url,
                headers=headers,
                payload=payload,
                timeout=timeout,
                max_bytes=max_bytes,
            )
            return {
                "id": "resp_123",
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {"type": "output_text", "text": '{"summary":"ok"}'}
                        ],
                    }
                ],
                "usage": {"input_tokens": 20, "output_tokens": 8},
            }

        provider = OpenAIResponsesProvider(
            base_url="https://api.openai.com/v1",
            api_key="unit-test-key",
            transport=transport,
        )
        model = AIModelDefinition(
            id=2,
            model_key="openai.test",
            provider_code="OPENAI",
            model_name="approved-model",
            display_name="Approved Model",
            deployment_type="HOSTED",
            supports_structured_output=True,
            max_output_tokens=500,
        )
        result = provider.generate_structured(self.request, model)

        self.assertEqual(captured["url"], "https://api.openai.com/v1/responses")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer unit-test-key")
        self.assertFalse(captured["payload"]["store"])
        self.assertEqual(
            captured["payload"]["text"]["format"]["type"],
            "json_schema",
        )
        self.assertTrue(captured["payload"]["text"]["format"]["strict"])
        self.assertEqual(result.payload, {"summary": "ok"})
        self.assertEqual(result.provider_request_id, "resp_123")

    def test_openai_adapter_does_not_call_transport_without_key(self) -> None:
        provider = OpenAIResponsesProvider(
            base_url="https://api.openai.com/v1",
            api_key="",
            transport=lambda *args: self.fail("transport must not be called"),
        )
        model = AIModelDefinition(
            id=2,
            model_key="openai.test",
            provider_code="OPENAI",
            model_name="approved-model",
            display_name="Approved Model",
            deployment_type="HOSTED",
            supports_structured_output=True,
        )
        with self.assertRaises(AIConfigurationError):
            provider.generate_structured(self.request, model)


if __name__ == "__main__":
    unittest.main()
