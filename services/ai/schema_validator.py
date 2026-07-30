"""Small dependency-free JSON Schema subset used for AI structured outputs."""
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from services.ai.errors import AIStructuredOutputError

_SUPPORTED_TYPES = {
    "object",
    "array",
    "string",
    "number",
    "integer",
    "boolean",
    "null",
}


def parse_json_response(raw_text: str) -> Any:
    """Parse one strict JSON document without accepting markdown wrappers."""
    text = str(raw_text or "").strip()
    if not text:
        raise AIStructuredOutputError("The AI provider returned an empty response.")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise AIStructuredOutputError(
            f"The AI provider did not return valid JSON at line {exc.lineno}, "
            f"column {exc.colno}."
        ) from exc


def validate_schema_definition(schema: Mapping[str, Any]) -> None:
    """Reject unsupported or unsafe schema definitions before provider use."""
    if not isinstance(schema, Mapping) or not schema:
        raise ValueError("A non-empty JSON output schema is required.")
    _validate_schema_node(schema, path="$", depth=0)


def validate_structured_output(payload: Any, schema: Mapping[str, Any]) -> None:
    """Validate a provider payload against RecruitOS' supported schema subset."""
    validate_schema_definition(schema)
    _validate_value(payload, schema, path="$", depth=0)


def _validate_schema_node(schema: Mapping[str, Any], *, path: str, depth: int) -> None:
    if depth > 20:
        raise ValueError(f"Schema nesting exceeds the RecruitOS limit at {path}.")
    if "$ref" in schema or "$defs" in schema or "definitions" in schema:
        raise ValueError("Schema references are not supported in this sprint.")

    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        if not schema_type or any(item not in _SUPPORTED_TYPES for item in schema_type):
            raise ValueError(f"Unsupported schema type at {path}.")
    elif schema_type not in _SUPPORTED_TYPES:
        raise ValueError(f"Schema type is required and must be supported at {path}.")

    if "enum" in schema:
        enum_values = schema["enum"]
        if not isinstance(enum_values, list) or not enum_values:
            raise ValueError(f"Schema enum must be a non-empty list at {path}.")

    types = set(schema_type if isinstance(schema_type, list) else [schema_type])
    if "object" in types:
        properties = schema.get("properties", {})
        if not isinstance(properties, Mapping):
            raise ValueError(f"Schema properties must be an object at {path}.")
        required = schema.get("required", [])
        if not isinstance(required, list) or any(not isinstance(item, str) for item in required):
            raise ValueError(f"Schema required must be a string list at {path}.")
        unknown = set(required) - set(properties)
        if unknown:
            raise ValueError(
                f"Required properties are not defined at {path}: {sorted(unknown)}"
            )
        for name, child in properties.items():
            if not isinstance(name, str) or not isinstance(child, Mapping):
                raise ValueError(f"Invalid property definition at {path}.")
            _validate_schema_node(child, path=f"{path}.{name}", depth=depth + 1)

    if "array" in types:
        items = schema.get("items")
        if not isinstance(items, Mapping):
            raise ValueError(f"Array schema requires an items schema at {path}.")
        _validate_schema_node(items, path=f"{path}[]", depth=depth + 1)


def _validate_value(value: Any, schema: Mapping[str, Any], *, path: str, depth: int) -> None:
    if depth > 30:
        raise AIStructuredOutputError(
            f"Structured output nesting exceeds the RecruitOS limit at {path}."
        )

    allowed = schema["type"]
    types = allowed if isinstance(allowed, list) else [allowed]
    if not any(_matches_type(value, schema_type) for schema_type in types):
        raise AIStructuredOutputError(
            f"Structured output type mismatch at {path}; expected {types}."
        )

    if "enum" in schema and value not in schema["enum"]:
        raise AIStructuredOutputError(
            f"Structured output value is not allowed at {path}."
        )
    if "const" in schema and value != schema["const"]:
        raise AIStructuredOutputError(
            f"Structured output value does not match the required constant at {path}."
        )

    if isinstance(value, Mapping):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        for name in required:
            if name not in value:
                raise AIStructuredOutputError(
                    f"Structured output is missing required property {path}.{name}."
                )
        if schema.get("additionalProperties") is False:
            extras = set(value) - set(properties)
            if extras:
                raise AIStructuredOutputError(
                    f"Structured output contains unsupported properties at {path}: "
                    f"{sorted(extras)}"
                )
        for name, child_schema in properties.items():
            if name in value:
                _validate_value(
                    value[name],
                    child_schema,
                    path=f"{path}.{name}",
                    depth=depth + 1,
                )

    if isinstance(value, list):
        minimum = int(schema.get("minItems", 0) or 0)
        maximum = schema.get("maxItems")
        if len(value) < minimum:
            raise AIStructuredOutputError(
                f"Structured output has fewer than {minimum} items at {path}."
            )
        if maximum is not None and len(value) > int(maximum):
            raise AIStructuredOutputError(
                f"Structured output has more than {int(maximum)} items at {path}."
            )
        item_schema = schema["items"]
        for index, item in enumerate(value):
            _validate_value(
                item,
                item_schema,
                path=f"{path}[{index}]",
                depth=depth + 1,
            )

    if isinstance(value, str):
        minimum = int(schema.get("minLength", 0) or 0)
        maximum = schema.get("maxLength")
        if len(value) < minimum:
            raise AIStructuredOutputError(
                f"Structured output text is shorter than {minimum} at {path}."
            )
        if maximum is not None and len(value) > int(maximum):
            raise AIStructuredOutputError(
                f"Structured output text is longer than {int(maximum)} at {path}."
            )

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if minimum is not None and value < minimum:
            raise AIStructuredOutputError(
                f"Structured output number is below the minimum at {path}."
            )
        if maximum is not None and value > maximum:
            raise AIStructuredOutputError(
                f"Structured output number is above the maximum at {path}."
            )


def _matches_type(value: Any, schema_type: str) -> bool:
    if schema_type == "object":
        return isinstance(value, Mapping)
    if schema_type == "array":
        return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))
    if schema_type == "string":
        return isinstance(value, str)
    if schema_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if schema_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if schema_type == "boolean":
        return isinstance(value, bool)
    if schema_type == "null":
        return value is None
    return False
