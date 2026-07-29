"""Audio transcription endpoint (optional feature)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from ..dependencies import TranscriptionServiceDep
from ..errors import AppError
from ..schemas import TranscribeResponse

router = APIRouter(tags=["transcription"])

# Serverless platforms cap request body size; keep uploads modest and document it.
_MAX_AUDIO_BYTES = 25 * 1024 * 1024  # 25 MB


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    service: TranscriptionServiceDep, file: Annotated[UploadFile, File()]
) -> TranscribeResponse:
    """Transcribe an uploaded audio file to text."""
    content = await file.read()
    if not content:
        raise AppError("The uploaded file is empty.", status_code=400, code="empty_file")
    if len(content) > _MAX_AUDIO_BYTES:
        raise AppError(
            f"Audio file exceeds the {_MAX_AUDIO_BYTES // (1024 * 1024)} MB limit.",
            status_code=413,
            code="file_too_large",
        )

    text = await service.transcribe(
        filename=file.filename or "audio",
        content=content,
        content_type=file.content_type or "application/octet-stream",
    )
    return TranscribeResponse(transcript=text)
