from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.zambretti.const import DOMAIN


@pytest.mark.asyncio
async def test_setup_component(hass: HomeAssistant) -> None:
    # Ensure the integration can be set up via async_setup_component without errors.
    assert await async_setup_component(hass, DOMAIN, {})
