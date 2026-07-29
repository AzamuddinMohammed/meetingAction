"""Analysis-provider selection.

Picks the concrete provider based on configuration: the direct Anthropic API when
``ANTHROPIC_API_KEY`` is set, otherwise OpenRouter when ``OPENROUTER_API_KEY`` is
set. Both implement the same ``AnalysisProvider`` protocol, so callers are
provider-agnostic.
"""

from __future__ import annotations

from ..config import Settings
from ._common import AnalysisProvider
from .claude import ClaudeService
from .openrouter import OpenRouterService


def get_analysis_service(settings: Settings) -> AnalysisProvider:
    if settings.claude_configured:
        return ClaudeService(settings)
    return OpenRouterService(settings)


def analysis_model_label(settings: Settings) -> str:
    """Human-readable model identifier for the response, per active provider."""
    if settings.claude_configured:
        return settings.claude_model
    if settings.openrouter_configured:
        return f"{settings.openrouter_model} (via OpenRouter)"
    return "unconfigured"
