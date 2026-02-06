import logging

from .const import ICON_MAPPING
from .helpers import safe_float

_LOGGER = logging.getLogger(__name__)


async def zambretti_forecast(
    pressure, fall, trend, current_wind_speed, temperature, normal_pressure
):
    """Determines the general forecast based on pressure, pressure trend, and temperature."""

    icon = "mdi:zend"
    alert_level = 0  # Default: No alert
    estimated_wind_speed = current_wind_speed  # Start with current speed

    # Adjust storm risk based on temperature
    temp_modifier = 0  # Adjusts storm severity
    if safe_float(temperature):
        _LOGGER.debug(f"Temperature used in Zambretti Forecast: {temperature}")
        if safe_float(temperature) > 25:
            temp_modifier = 1  # Warmer air increases storm strength
        elif safe_float(temperature) < 5:
            temp_modifier = -1  # Cold air stabilizes high pressure, reduces storm risk

    _LOGGER.debug(f"ZF temp_modifier: {temp_modifier}")
    _LOGGER.debug(f"ZF trend: {trend}")
    _LOGGER.debug(f"ZF pressure: {pressure}")

    # Apply Zambretti Forecasting Logic
    forecast = ""
    if trend == "rising":
        if pressure > normal_pressure + 5:
            forecast += "Clear(ish) skies, little to no rain, mild temperatures"
            icon = ICON_MAPPING[0][0]
            alert_level = max(0, alert_level + temp_modifier)  # Reduce alert if cold
            estimated_wind_speed = max(5, current_wind_speed - 3)
        elif pressure > normal_pressure - 5:
            forecast += "Stable, calm, and pleasant weather, possible light clouds"
            icon = ICON_MAPPING[1][0]
            alert_level = max(0, alert_level + temp_modifier)
            estimated_wind_speed = max(5, current_wind_speed - 2)
        else:
            forecast += "Improving conditions, clearing skies"
            icon = ICON_MAPPING[2][0]
            alert_level = max(0, alert_level + temp_modifier)
            estimated_wind_speed = max(10, current_wind_speed)

    elif trend == "steady":
        if pressure > normal_pressure + 5:
            forecast += "Continued fair, calm and predictable weather"
            icon = ICON_MAPPING[0][0]
            alert_level = max(0, alert_level + temp_modifier)
            estimated_wind_speed = max(
                5, current_wind_speed
            )  # 5-12 knots, light breeze
        elif pressure > normal_pressure - 5:
            forecast += "Fair weather with occasional clouds"
            icon = ICON_MAPPING[1][0]
            alert_level = max(0, alert_level + temp_modifier)
            estimated_wind_speed = max(8, current_wind_speed)  # 8-15 knots, steady
        else:
            forecast += "Changeable weather, gusty winds, possible rain later"
            icon = ICON_MAPPING[3][0]
            alert_level = max(1, alert_level + temp_modifier)
            estimated_wind_speed = max(12, current_wind_speed + 3)  # 12-18 knots

    elif trend == "falling":
        if pressure > normal_pressure + 5:
            forecast += "Possible deterioration, watch for winds"
            icon = ICON_MAPPING[2][0]
            alert_level = max(1, alert_level + temp_modifier)
            estimated_wind_speed = max(15, current_wind_speed + 5)
        elif pressure > normal_pressure - 5:
            forecast += "Changeable weather, gusty winds, increasing cloud cover"
            icon = ICON_MAPPING[4][0]
            alert_level = max(2, alert_level + temp_modifier)
            estimated_wind_speed = max(20, current_wind_speed + 8)
        else:
            forecast += "Stormy conditions likely, heavy rain expected"
            if temperature < 0:
                forecast += " ❄️ Possible snow instead of rain"
            icon = ICON_MAPPING[5][0]
            alert_level = max(3, alert_level + temp_modifier)
            estimated_wind_speed = max(25, current_wind_speed + 12)

    elif trend == "falling_fast":
        if pressure > normal_pressure - 10:
            forecast += "Windy, rain likely"
            icon = ICON_MAPPING[4][0]
            alert_level = max(3, alert_level + temp_modifier)
            estimated_wind_speed = max(25, current_wind_speed + 12)
        elif pressure > normal_pressure - 15:
            forecast += "Strong winds, rain, possible squalls"
            if temperature < 0:
                forecast += " ❄️ Snowstorm possible"
            icon = ICON_MAPPING[4][0]
            alert_level = max(4, alert_level + temp_modifier)
            estimated_wind_speed = max(30, current_wind_speed + 15)
        else:
            forecast += "Very low pressure. Dangerous weather, high winds, big waves"
            icon = ICON_MAPPING[6][0]
            alert_level = max(5, alert_level + temp_modifier)
            estimated_wind_speed = max(40, current_wind_speed + 25)

    elif trend == "plummeting":
        if pressure > normal_pressure - 10:
            forecast += "Strong winds, thunderstorms, possible storm system"
            if temperature < 0:
                forecast += "Blizzard conditions possible."
            icon = ICON_MAPPING[6][0]
            alert_level = max(4, alert_level + temp_modifier)
            estimated_wind_speed = max(30, current_wind_speed + 20)
        elif pressure > normal_pressure - 15:
            forecast += "Low pressure. Major storm system, possible gale-force winds"
            icon = ICON_MAPPING[7][0]
            alert_level = max(5, alert_level + temp_modifier)
            estimated_wind_speed = max(40, current_wind_speed + 25)
        else:
            forecast += "Very low pressure. Severe weather, hurricane/cyclone possible"
            icon = ICON_MAPPING[7][0]
            alert_level = max(5, alert_level + temp_modifier)
            estimated_wind_speed = max(50, current_wind_speed + 30)

    _LOGGER.debug(f"ZF forecast: {forecast}")

    estimated_max_wind_speed = round(safe_float(estimated_wind_speed) * 1.2)

    return forecast, icon, alert_level, estimated_wind_speed, estimated_max_wind_speed
