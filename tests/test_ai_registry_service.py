"""AI registry authorization, isolation, and audit tests."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from database.user_repository import UserRepository
from services.ai_registry_service import AIRegistryService
from services.authorization_service import READER, TENANT_ADMIN, USER
from tests.security_test_utils import create_context, create_owner_context


SCHEMA = {
    "type": "object",
    "properties": {"summary": {"type": "string"}},
    "required": ["summary"],
    "additionalProperties": False,
}


class AIRegistryServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp.name) / "recruitos.db"
        self.owner = create_owner_context(self.database_path)
        self.user = create_context(
            self.database_path,
            "ai.user@example.com",
            "AI User",
            user_id="AI-USER",
            role=USER,
        )
        self.other_user = create_context(
            self.database_path,
            "other.ai.user@example.com",
            "Other AI User",
            user_id="AI-OTHER",
            role=USER,
            country_location="Germany - Munich",
        )
        self.reader = create_context(
            self.database_path,
            "ai.reader@example.com",
            "AI Reader",
            user_id="AI-READER",
            role=READER,
        )
        self.service = AIRegistryService(self.database_path)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _register_active_assets(self):
        model = self.service.register_model(
            self.owner,
            model_key="ollama.registry-test",
            provider_code="OLLAMA",
            model_name="registry-test-model",
            display_name="Registry Test Model",
            input_cost_per_million_usd=0.0,
            output_cost_per_million_usd=0.0,
            context_window=16000,
            max_output_tokens=1000,
        )
        prompt = self.service.create_prompt_version(
            self.owner,
            prompt_key="test.registry-prompt",
            task_code="TEST_TASK",
            system_template="Return structured evidence.",
            user_template="Input: $document_text",
            output_schema=SCHEMA,
            activate=True,
        )
        return model, prompt

    def test_owner_registers_model_prompt_and_policy_without_secret_fields(self) -> None:
        model, prompt = self._register_active_assets()
        policy = self.service.set_policy(
            self.owner,
            target_user_id=self.user.user_id,
            task_code="TEST_TASK",
            model_id=model["id"],
            prompt_version_id=prompt["id"],
            enabled=True,
            allow_external_data=False,
        )

        self.assertEqual(policy["model_key"], "ollama.registry-test")
        self.assertEqual(policy["prompt_key"], "test.registry-prompt")
        self.assertNotIn("api_key", model)
        self.assertNotIn("credential", policy)

        repository = UserRepository(self.database_path)
        try:
            audit = repository.list_audit_events(limit=50)
        finally:
            repository.close()
        actions = {item["action"] for item in audit}
        self.assertIn("AI_MODEL_REGISTERED", actions)
        self.assertIn("AI_PROMPT_VERSION_CREATED", actions)
        self.assertIn("AI_TENANT_POLICY_UPDATED", actions)

    def test_user_can_view_own_policy_but_cannot_manage_registry(self) -> None:
        model, prompt = self._register_active_assets()
        self.service.set_policy(
            self.owner,
            target_user_id=self.user.user_id,
            task_code="TEST_TASK",
            model_id=model["id"],
            prompt_version_id=prompt["id"],
        )
        own = self.service.get_policy(self.user, task_code="TEST_TASK")
        self.assertIsNotNone(own)
        self.assertNotIn("system_template", own)
        self.assertNotIn("user_template", own)
        self.assertNotIn("output_schema", own)
        prompt_metadata = self.service.list_prompt_versions(self.user)
        self.assertNotIn("system_template", prompt_metadata[0])

        with self.assertRaises(PermissionError):
            self.service.register_model(
                self.user,
                model_key="ollama.unauthorized",
                provider_code="OLLAMA",
                model_name="unauthorized",
                display_name="Unauthorized",
            )
        with self.assertRaises(PermissionError):
            self.service.get_policy(
                self.user,
                task_code="TEST_TASK",
                target_user_id=self.other_user.user_id,
            )

    def test_reader_has_no_ai_policy_permission(self) -> None:
        with self.assertRaises(PermissionError):
            self.service.list_models(self.reader)

    def test_tenant_admin_is_limited_to_country_location(self) -> None:
        tenant_admin = create_context(
            self.database_path,
            "ai.admin@example.com",
            "AI Tenant Admin",
            user_id="AI-TENANT-ADMIN",
            role=TENANT_ADMIN,
        )
        model, prompt = self._register_active_assets()
        policy = self.service.set_policy(
            tenant_admin,
            target_user_id=self.user.user_id,
            task_code="TEST_TASK",
            model_id=model["id"],
            prompt_version_id=prompt["id"],
        )
        self.assertEqual(policy["target_user_id"], self.user.user_id)

        with self.assertRaises(PermissionError):
            self.service.set_policy(
                tenant_admin,
                target_user_id=self.other_user.user_id,
                task_code="TEST_TASK",
                model_id=model["id"],
                prompt_version_id=prompt["id"],
            )

    def test_prompt_versions_are_immutable_and_activation_retires_previous(self) -> None:
        self._register_active_assets()
        second = self.service.create_prompt_version(
            self.owner,
            prompt_key="test.registry-prompt",
            task_code="TEST_TASK",
            system_template="Second system prompt.",
            user_template="Second: $document_text",
            output_schema=SCHEMA,
            activate=True,
        )
        prompts = self.service.list_prompt_versions(self.owner)
        matching = [item for item in prompts if item["prompt_key"] == "test.registry-prompt"]
        self.assertEqual(len(matching), 2)
        self.assertEqual(second["version_number"], 2)
        self.assertEqual(sum(item["status"] == "ACTIVE" for item in matching), 1)


if __name__ == "__main__":
    unittest.main()
