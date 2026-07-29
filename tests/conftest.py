"""Shared pytest fixtures.

The app is built fresh per test with a clean settings cache so environment
monkeypatching is honored, and services are overridden with fakes so no network
calls or real API keys are needed.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from server.config import get_settings
from server.main import create_app


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)
