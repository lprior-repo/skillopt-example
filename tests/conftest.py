"""Test configuration: sys.path setup and custom pytest marker registration."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT: Path = Path(__file__).resolve().parents[1]

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def pytest_configure(config: pytest.Config) -> None:
    """Register the custom pytest markers used by the property tests."""
    config.addinivalue_line("markers", "property: hypothesis property test marker")
