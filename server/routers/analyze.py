"""Meeting analysis endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from ..dependencies import AnalysisServiceDep, SettingsDep
from ..errors import AppError
from ..schemas import AnalyzeRequest, AnalyzeResponse
from ..services.analysis import analysis_model_label

router = APIRouter(tags=["analysis"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    req: AnalyzeRequest, service: AnalysisServiceDep, settings: SettingsDep
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
    return AnalyzeResponse(
        analysis=analysis, model=analysis_model_label(settings), usage=usage
    )
