"""
Test configuration for plaud_mcp.

IMPORTANT: env vars are set at module level (before any imports) so that
pydantic-settings' Settings() instantiation at import time does not raise
a ValidationError during test collection. The autouse fixture also sets them
for completeness and to handle any lazy re-instantiation.
"""
import os

# Must be set before test modules import plaud_mcp.config (which calls Settings())
os.environ.setdefault("PLAUD_TOKEN", "test-token-abc123")
os.environ.setdefault("PLAUD_DEVICE_ID", "test-device-uuid-001")

import pytest


@pytest.fixture(autouse=True)
def plaud_env_vars(monkeypatch):
    """Inject required env vars so Settings() does not raise during tests."""
    monkeypatch.setenv("PLAUD_TOKEN", "test-token-abc123")
    monkeypatch.setenv("PLAUD_DEVICE_ID", "test-device-uuid-001")
