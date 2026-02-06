"""Regions configuration for Zambretti integration."""

import logging

from .dictionaries import (
    REGION_CATALOG,
    WIND_SYSTEM_CATALOG,
    WIND_SYSTEM_INDEX,
)
from .helpers import safe_float

_LOGGER = logging.getLogger(__name__)


def wind_systems(
    region, region_name, region_url, latitude, longitude, wind_direction, wind_speed
):
    """Determine the most relevant wind system based on region, wind direction, and location."""

    _LOGGER.debug(f"WIND_SYSTEMS: {region}  {region_url}")
    default_description = REGION_CATALOG.get(region, {}).get(
        wind_direction, "No wind description available."
    )
    default_url = f'<a href="{region_url}">{region_name}</a>'
    _LOGGER.debug(f"WIND_SYSTEMS: {default_url}")

    # ✅ Step 1: Handle low wind speeds
    if safe_float(wind_speed) < 3:
        _LOGGER.debug("Wind speed < 5, so default description applies.")
        return default_description, default_url

    wind_systems_for_region = []
    # ✅ Step 2: Get possible wind systems based on wind direction
    if region in WIND_SYSTEM_INDEX and wind_direction in WIND_SYSTEM_INDEX[region]:
        wind_systems_for_region = WIND_SYSTEM_INDEX[region][wind_direction]
        _LOGGER.debug(
            f"🌬 Possible wind systems for {wind_direction} in {region}: {wind_systems_for_region}"
        )
    else:
        _LOGGER.debug(f"⚠️ No wind systems found for {wind_direction} in {region}.")

    # ✅ Step 3: If no wind system found, return the default description
    if not wind_systems_for_region:
        return f"No systems in region, so {default_description}", default_url

    # ✅ Step 4: Check which wind systems apply based on coordinates
    descriptions = []
    urls = []
    for wind_system in wind_systems_for_region:
        if wind_system in WIND_SYSTEM_CATALOG:
            bounds, system_desc, system_url = WIND_SYSTEM_CATALOG[
                wind_system
            ]  # Extract bounds & description
            lat_min, lat_max, lon_min, lon_max = bounds  # Unpack bounds

            _LOGGER.debug(
                f"Checking {wind_system}: Bounds {bounds} for location ({latitude}, {longitude})"
            )

            # Check if the coordinates fall within the wind system's bounds
            if lat_min <= latitude <= lat_max and lon_min <= longitude <= lon_max:
                descriptions.append(
                    f"{wind_system}: {system_desc}"
                )  # ✅ Valid wind system for this location
                urls.append(f'<a href="{system_url}">{wind_system}</a>')
                _LOGGER.debug(f'✅ Match: <a href="{system_url}">{wind_system}</a>')

    # ✅ Step 5: If matching wind systems found, return them
    if descriptions:
        _LOGGER.debug(f"✅ Matching wind systems: {descriptions}")
        urls.append(default_url)
        return "\n".join(descriptions), " ".join(
            urls
        )  # Return the matched wind systems

    _LOGGER.warning(
        f"⚠️ No specific wind system found for {wind_direction} in {region}. Using default with {default_url}"
    )

    # ✅ Step 6: Return default wind description if no specific wind system applies
    return default_description, default_url
