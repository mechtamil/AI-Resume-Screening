"""Typed errors for the RecruitOS AI gateway."""
from __future__ import annotations


class AIError(RuntimeError):
    """Base class for controlled AI gateway failures."""

    error_code = "AI_ERROR"


class AIConfigurationError(AIError):
    error_code = "AI_CONFIGURATION_ERROR"


class AIPolicyError(AIError):
    error_code = "AI_POLICY_ERROR"


class AIProviderError(AIError):
    error_code = "AI_PROVIDER_ERROR"


class AIStructuredOutputError(AIError):
    error_code = "AI_STRUCTURED_OUTPUT_ERROR"
