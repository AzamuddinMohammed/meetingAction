"""Vercel serverless entrypoint.

Vercel's Python runtime looks for an ASGI ``app`` in this module. We add the
repository root to ``sys.path`` so the ``server`` package (kept at the repo root
for clean local development and testing) is importable inside the function bundle.
The ``server/**`` files are pulled into the bundle via ``includeFiles`` in
``vercel.json``.
"""

from __future__ import annotations

import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from server.main import app  # noqa: E402

__all__ = ["app"]
