from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure repo root (containing custom_components/) is importable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations):
    """Enable loading this repo's custom_components via HA loader."""
    yield
