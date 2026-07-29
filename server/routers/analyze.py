"""Meeting analysis endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from ..dependencies import ClaudeServiceDep, SettingsDep
from ..errors import AppError
from ..schemas import AnalyzeRequest, AnalyzeResponse

router = APIRouter(tags=["analysis"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    req: AnalyzeRequest, service: ClaudeServiceDep, settings: SettingsDep
) -> AnalyzeResponse:
    """Turn a transcript into a structured meeting record."""
    if len(req.transcript) > settings.max_transcript_chars:
        raise AppError(
            f"Transcript exceeds the maximum of {settings.max_transcript_chars} characters. "
            "Split it into shorter segments.",
            status_code=413,
            code="transcript_too_large",
        )

    analysis, usage = await service.analyze(req)
    return AnalyzeResponse(analysis=analysis, model=settings.claude_model, usage=usage)
