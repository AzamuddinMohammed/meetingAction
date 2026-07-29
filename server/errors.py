"""Typed application errors and a consistent JSON error envelope."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base class for expected, user-facing failures.

    Carries an HTTP status and a machine-readable code so the frontend can
    branch on failure modes without string-matching messages.
    """

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, *, status_code: int | None = None, code: str | None = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code


class FeatureUnavailableError(AppError):
    status_code = 503
    code = "feature_unavailable"


class UpstreamError(AppError):
    """A dependency (Claude, Jira, Notion, OpenAI) failed or returned an error."""

    status_code = 502
    code = "upstream_error"


class ContentRefusedError(AppError):
    """Claude declined to process the request for safety reasons."""

    status_code = 422
    code = "content_refused"


def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )
