"""Context-local configuration selection for concurrent RecruitOS users."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator

from models.configuration_version import ConfigurationSelection


_CURRENT_CONFIGURATION: ContextVar[ConfigurationSelection | None] = ContextVar(
    "recruitos_current_configuration",
    default=None,
)


class ConfigurationContext:
    """Provide request-local configuration without process-global mutable state."""

    @staticmethod
    def current() -> ConfigurationSelection | None:
        return _CURRENT_CONFIGURATION.get()

    @classmethod
    @contextmanager
    def activate(cls, selection: ConfigurationSelection) -> Iterator[ConfigurationSelection]:
        selection.require_valid()
        token: Token[ConfigurationSelection | None] = _CURRENT_CONFIGURATION.set(selection)
        try:
            yield selection
        finally:
            _CURRENT_CONFIGURATION.reset(token)
