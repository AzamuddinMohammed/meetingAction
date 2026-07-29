"""Health and capability reporting."""

from __future__ import annotations

from fastapi import APIRouter

from .. import __version__
from ..dependencies import SettingsDep
from ..schemas import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health(settings: SettingsDep) -> HealthResponse:
    """Liveness probe plus a map of which optional features are configured.

    The frontend reads ``features`` to enable/disable UI (e.g. hide the Jira
    export button when Jira isn't set up).
    """
    return HealthResponse(
        status="ok",
        version=__version__,
        features={
            "analysis": settings.claude_configured,
            "transcription": settings.transcription_configured,
            "jira_export": settings.jira_configured,
            "notion_export": settings.notion_configured,
        },
    )
