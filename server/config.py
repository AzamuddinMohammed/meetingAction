"""Application configuration, loaded from environment variables.

All settings are optional at import time so the app can boot in any environment
(local dev, CI, Vercel) without secrets. Feature availability is derived from
which credentials are present — see the `*_configured` properties.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Effort = Literal["low", "medium", "high", "xhigh", "max"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Core / Claude (direct Anthropic API) ---
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    claude_model: str = Field(default="claude-opus-4-8", alias="CLAUDE_MODEL")
    analysis_effort: Effort = Field(default="medium", alias="ANALYSIS_EFFORT")
    analysis_max_tokens: int = Field(default=8000, alias="ANALYSIS_MAX_TOKENS")

    # --- Alternative provider: OpenRouter (OpenAI-compatible gateway to Claude) ---
    # Used automatically when ANTHROPIC_API_KEY is absent but OPENROUTER_API_KEY is set.
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(
        default="anthropic/claude-sonnet-4.5", alias="OPENROUTER_MODEL"
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL"
    )
    # Optional attribution headers OpenRouter uses for its dashboard/rankings.
    openrouter_site_url: str | None = Field(default=None, alias="OPENROUTER_SITE_URL")
    openrouter_app_title: str = Field(
        default="MeetingAction", alias="OPENROUTER_APP_TITLE"
    )

    # --- HTTP / CORS ---
    # Comma-separated list of allowed origins. "*" allows all (dev default).
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")
    request_timeout_seconds: float = Field(default=120.0, alias="REQUEST_TIMEOUT_SECONDS")
    max_transcript_chars: int = Field(default=200_000, alias="MAX_TRANSCRIPT_CHARS")

    # --- Optional transcription (OpenAI Whisper) ---
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    transcription_model: str = Field(
        default="whisper-1", alias="TRANSCRIPTION_MODEL"
    )

    # --- Optional Jira integration ---
    jira_base_url: str | None = Field(default=None, alias="JIRA_BASE_URL")
    jira_email: str | None = Field(default=None, alias="JIRA_EMAIL")
    jira_api_token: str | None = Field(default=None, alias="JIRA_API_TOKEN")
    jira_project_key: str | None = Field(default=None, alias="JIRA_PROJECT_KEY")
    jira_issue_type: str = Field(default="Task", alias="JIRA_ISSUE_TYPE")

    # --- Optional Notion integration ---
    notion_api_key: str | None = Field(default=None, alias="NOTION_API_KEY")
    notion_database_id: str | None = Field(default=None, alias="NOTION_DATABASE_ID")

    @property
    def claude_configured(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def openrouter_configured(self) -> bool:
        return bool(self.openrouter_api_key)

    @property
    def analysis_configured(self) -> bool:
        """True if any analysis provider (Anthropic or OpenRouter) is available."""
        return self.claude_configured or self.openrouter_configured

    @property
    def analysis_provider(self) -> str:
        """Which provider will be used. Anthropic is preferred when both are set."""
        if self.claude_configured:
            return "anthropic"
        if self.openrouter_configured:
            return "openrouter"
        return "none"

    @property
    def transcription_configured(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def jira_configured(self) -> bool:
        return all(
            [
                self.jira_base_url,
                self.jira_email,
                self.jira_api_token,
                self.jira_project_key,
            ]
        )

    @property
    def notion_configured(self) -> bool:
        return bool(self.notion_api_key and self.notion_database_id)

    @property
    def cors_origin_list(self) -> list[str]:
        raw = self.cors_origins.strip()
        if raw == "*" or not raw:
            return ["*"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Cached so the environment is read once per process. Tests can clear the
    cache via `get_settings.cache_clear()` after monkeypatching env vars.
    """
    return Settings()
