"""RecruitOS AI gateway foundation.

No screening flow calls external AI until a tenant policy is explicitly enabled.
"""

from services.ai.errors import (
    AIConfigurationError,
    AIError,
    AIPolicyError,
    AIProviderError,
    AIStructuredOutputError,
)

__all__ = [
    "AIError",
    "AIConfigurationError",
    "AIPolicyError",
    "AIProviderError",
    "AIStructuredOutputError",
]
