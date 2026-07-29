"""FastAPI dependency providers.

Services are constructed per-request from cached settings. They're cheap to build
(no network at construction time), which keeps them easy to override in tests via
``app.dependency_overrides``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from .config import Settings, get_settings
from .services.claude import ClaudeService
from .services.jira import JiraService
from .services.notion import NotionService
from .services.transcription import TranscriptionService

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_claude_service(settings: SettingsDep) -> ClaudeService:
    return ClaudeService(settings)


def get_transcription_service(settings: SettingsDep) -> TranscriptionService:
    return TranscriptionService(settings)


def get_jira_service(settings: SettingsDep) -> JiraService:
    return JiraService(settings)


def get_notion_service(settings: SettingsDep) -> NotionService:
    return NotionService(settings)


ClaudeServiceDep = Annotated[ClaudeService, Depends(get_claude_service)]
TranscriptionServiceDep = Annotated[TranscriptionService, Depends(get_transcription_service)]
JiraServiceDep = Annotated[JiraService, Depends(get_jira_service)]
NotionServiceDep = Annotated[NotionService, Depends(get_notion_service)]
