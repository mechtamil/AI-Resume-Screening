"""Tests for dependency-free structured-output validation."""
from __future__ import annotations

import unittest

from services.ai.errors import AIStructuredOutputError
from services.ai.schema_validator import (
    parse_json_response,
    validate_schema_definition,
    validate_structured_output,
)


SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "score": {"type": "number", "minimum": 0, "maximum": 100},
        "skills": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
    },
    "required": ["name", "score", "skills"],
    "additionalProperties": False,
}


class AISchemaValidatorTests(unittest.TestCase):
    def test_valid_payload_passes(self) -> None:
        validate_structured_output(
            {"name": "Candidate", "score": 88.5, "skills": ["Python"]},
            SCHEMA,
        )

    def test_missing_required_property_fails(self) -> None:
        with self.assertRaisesRegex(AIStructuredOutputError, "missing required"):
            validate_structured_output(
                {"name": "Candidate", "score": 88.5},
                SCHEMA,
            )

    def test_additional_property_fails(self) -> None:
        with self.assertRaisesRegex(AIStructuredOutputError, "unsupported properties"):
            validate_structured_output(
                {
                    "name": "Candidate",
                    "score": 88.5,
                    "skills": ["Python"],
                    "secret": "not allowed",
                },
                SCHEMA,
            )

    def test_invalid_json_is_rejected(self) -> None:
        with self.assertRaisesRegex(AIStructuredOutputError, "valid JSON"):
            parse_json_response("```json\n{}\n```")

    def test_schema_references_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "references are not supported"):
            validate_schema_definition(
                {
                    "type": "object",
                    "$defs": {"name": {"type": "string"}},
                    "properties": {},
                }
            )


if __name__ == "__main__":
    unittest.main()
