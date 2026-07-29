"""FastAPI application factory.

All routes live under the ``/api`` prefix so the same paths work locally and on
Vercel (which rewrites ``/api/*`` to the Python serverless function).
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import get_settings
from .errors import AppError, app_error_handler
from .routers import analyze, export, health, transcribe

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="MeetingAction API",
        version=__version__,
        description=(
            "Turn meeting transcripts into structured summaries, decisions, "
            "action items, and follow-up emails — with optional Jira/Notion sync."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppError, app_error_handler)

    for module in (health, analyze, transcribe, export):
        app.include_router(module.router, prefix="/api")

    return app


app = create_app()
