"""Analyze humidity an temperature, establish chance of fog"""

import logging
import math

from .helpers import safe_float

_LOGGER = logging.getLogger(__name__)


def determine_fog_chance(
    p_humidity, p_temperature, p_wind_speed, fog_area_type="normal"
):
    """Improved fog probability calculation with realistic adjustments for temperature & wind."""

    _LOGGER.debug(f"Startup: t={p_temperature}, h={p_humidity}, w={p_wind_speed}")

    # Convert inputs to safe floats
    humidity = safe_float(p_humidity)
    temperature = safe_float(p_temperature)
    wind_speed = safe_float(p_wind_speed)

    _LOGGER.debug(f"Step2: t={temperature}, h={humidity}, w={wind_speed}")

    # Validate input (humidity and temperature must be valid)
    if humidity == 0 or temperature is None:
        _LOGGER.debug(f"Invalid sensors. t={temperature}, h={humidity}, w={wind_speed}")
        return "No valid sensor data.", 0, 0, 0, 0

    alert_level = 0

    # Logging inputs
    _LOGGER.debug(
        f"Calculating fog chance with Humidity: {humidity}%, Temperature: {temperature}°C, Wind Speed: {wind_speed} km/h"
    )

    if humidity < 20:
        return "No chance of fog. Air is too dry.", 0, 0, 0, 0  # No fog possible.

    # Calculate dew point (Magnus-Tetens formula)
    alpha = (17.27 * temperature) / (237.7 + temperature) + math.log(humidity / 100)
    dewpoint = (237.7 * alpha) / (17.27 - alpha)

    # Temperature difference from dew point
    temp_diff = round(temperature - dewpoint, 1)

    # **🔹 Updated Fog Probability Formula**
    if temp_diff > 6:
        fog_probability = 0  # Fog nearly impossible
    elif temp_diff > 3:
        fog_probability = max(0, 100 - 15 * temp_diff)  # More aggressive reduction
    else:
        fog_probability = max(0, 100 - 8 * temp_diff)  # Normal reduction

    # **🔹 More Realistic Temperature Scaling**
    if temperature > 35:
        fog_probability = 0  # Too hot for fog
    elif temperature > 30:
        fog_probability *= 0.1  # Almost no chance
    elif temperature > 25:
        fog_probability *= 0.3  # Strongly reduced
    elif temperature > 20:
        fog_probability *= 0.7  # Reduced, but still possible

    # **🔹 More Realistic Wind Effect**
    if wind_speed > 20:
        fog_probability *= 0.1  # Strong winds eliminate fog
    elif wind_speed > 15:
        fog_probability *= 0.2  # Very low fog chance
    elif wind_speed > 10:
        fog_probability *= 0.4  # Moderately reduces fog
    elif wind_speed > 5:
        fog_probability *= 0.7  # Small reduction
    # Below 5 km/h, no additional change (calm air)

    # **Adjust Fog Probability Based on Location Type**
    fog_area_adjustments = {
        "frequent_dense_fog": 1.5,  # 50% increase
        "fog_prone": 1.2,  # 20% increase
        "normal": 1.0,  # No change
        "rare_fog": 0.7,  # 30% decrease
        "hardly_ever_fog": 0.4,  # 60% decrease
    }

    # Apply location-based adjustment
    fog_probability *= fog_area_adjustments.get(fog_area_type, 1.0)

    # **🔹 Ensure probability remains between 0% and 100%**
    fog_probability = int(max(0, min(100, fog_probability)))

    # **🔹 Adjust Fog Description Based on Probability**
    if fog_probability > 90:
        fog_likelihood = "Fog is very likely"
    elif fog_probability > 70:
        fog_likelihood = "Fog is possible"
    elif fog_probability > 40:
        fog_likelihood = "Fog is unlikely"
    elif fog_probability > 10:
        fog_likelihood = "Fog is very unlikely"
    else:
        fog_likelihood = "No fog expected"

    fog_dec_probability = round(fog_probability / 10) * 10
    #    fog_likelihood += f"({fog_dec_probability}% chance, {diff_txt})."

    # **🔹 Additional Behavior Based on Wind**
    if fog_probability > 90:
        fog_likelihood += (
            ", trong winds soon clear it" if wind_speed > 15 else " It may persist"
        )
        alert_level = 3
    elif fog_probability > 60:
        fog_likelihood += ", ind reduces fog" if wind_speed > 10 else " It may persist"

    # **🔹 Improved Logging**
    _LOGGER.debug(
        f"Fog Probability: {fog_probability}%, Dew Point: {dewpoint:.2f}°C, Temp Diff: {temp_diff:.2f}°C, Alert Level: {alert_level}"
    )

    return fog_likelihood, fog_dec_probability, dewpoint, temp_diff, alert_level
