import os

import pytest


@pytest.fixture(autouse=True)
def _disable_paid_apis_by_default(monkeypatch):
    """Keep unit tests offline and free unless a test opts in."""
    monkeypatch.setenv("USE_CLAUDE", "0")
    monkeypatch.setenv("USE_BRIGHTDATA", "0")
