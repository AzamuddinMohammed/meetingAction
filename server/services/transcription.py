"""Optional audio transcription via OpenAI Whisper.

Kept behind a feature flag: if ``OPENAI_API_KEY`` is not set the endpoint reports
the feature as unavailable rather than failing opaquely. Anthropic's API does not
transcribe audio, so this is the pragmatic way to support audio input while
keeping the analysis pipeline Claude-first.
"""

from __future__ import annotations

import logging

import httpx

from ..config import Settings
from ..errors import FeatureUnavailableError, UpstreamError

logger = logging.getLogger(__name__)

_OPENAI_TRANSCRIBE_URL = "https://api.openai.com/v1/audio/transcriptions"


class TranscriptionService:
    def __init__(self, settings: Settings):
        self._settings = settings

    async def transcribe(self, filename: str, content: bytes, content_type: str) -> str:
        if not self._settings.transcription_configured:
            raise FeatureUnavailableError(
                "Audio transcription is unavailable: OPENAI_API_KEY is not configured. "
                "Paste the transcript text instead."
            )

        headers = {"Authorization": f"Bearer {self._settings.openai_api_key}"}
        files = {"file": (filename, content, content_type or "application/octet-stream")}
        data = {"model": self._settings.transcription_model}

        try:
            async with httpx.AsyncClient(timeout=self._settings.request_timeout_seconds) as client:
                resp = await client.post(
                    _OPENAI_TRANSCRIBE_URL, headers=headers, files=files, data=data
                )
        except httpx.HTTPError as exc:
            logger.warning("Transcription request failed: %s", exc)
            raise UpstreamError("Could not reach the transcription provider.") from exc

        if resp.status_code >= 400:
            logger.warning("Transcription error %s: %s", resp.status_code, resp.text[:500])
            raise UpstreamError(
                f"The transcription provider returned an error ({resp.status_code})."
            )

        payload = resp.json()
        text = payload.get("text", "")
        if not text:
            raise UpstreamError("The transcription provider returned no text.")
        return text
