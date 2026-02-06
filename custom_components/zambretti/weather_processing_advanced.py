import calendar
import logging
from datetime import datetime, timedelta

import numpy as np
from homeassistant.components.recorder import history
from homeassistant.util import dt as dt_util

from .dictionaries import MONTHLY_NORMALS_BY_REGION
from .helpers import safe_float

_LOGGER = logging.getLogger(__name__)
# _LOGGER.setLevel(logging.DEBUG)  # Or use logging.INFO for less verbosity


async def generate_pressure_forecast_advanced(
    hass, entity_id, current_pressure, region, short=False
):
    # Monthly averages (should be defined outside function ideally)
    region_normals = MONTHLY_NORMALS_BY_REGION.get(region)

    if not region_normals:
        return f"❌ Region '{region}' not found in pressure normals."

    # Get month here, no pass as variable
    month = datetime.now().month
    month_name = calendar.month_abbr[month]  # 'Apr'

    # Get normal pressure for this month and region
    normal = region_normals.get(month, 1015)
    anomaly = current_pressure - normal

    # Classify anomaly
    if anomaly > 5:
        pressure_context = "Unusually high — very stable"
    elif anomaly > 2:
        pressure_context = "Slightly above average — settled"
    elif anomaly > -2:
        pressure_context = "Near seasonal average — normal variability"
    elif anomaly > -5:
        pressure_context = "Below average — increasing instability"
    else:
        pressure_context = "Unusually low — stormy pattern likely"

    # Get pressure trends in hPa/hr
    trend_3h = await get_trend(hass, entity_id, 3)
    trend_6h = await get_trend(hass, entity_id, 6)
    trend_12h = await get_trend(hass, entity_id, 12)

    # Trend classification
    def classify_trend(trend):
        if trend > 1.0:
            return "↑↑↑ (rising rapidly)"
        elif trend > 0.5:
            return "↑↑ (rising fast)"
        elif trend > 0.1:
            return "↑ (rising)"
        elif trend > -0.1:
            return "→ (steady)"
        elif trend > -0.5:
            return "↓ (falling)"
        elif trend > -1.0:
            return "↓↓ (falling fast)"
        else:
            return "⬇⬇⬇ (plummeting)"

    trend_labels = {
        "3h": classify_trend(trend_3h),
        "6h": classify_trend(trend_6h),
        "12h": classify_trend(trend_12h),
    }

    # Forecast summary & warning level
    if trend_3h < -1.0:
        trend_summary = (
            "Pressure is plummeting — very likely a storm or squall incoming."
        )
        warning_level = 5
    elif trend_3h < -0.5 and trend_6h < -0.5 and trend_12h < -0.5:
        trend_summary = (
            "Consistent strong fall — stormy or worsening weather is very likely."
        )
        warning_level = 4
    elif trend_3h > 0.5 and trend_6h > 0.5 and trend_12h > 0.5:
        trend_summary = "Strong and consistent rise — improving and settled weather."
        warning_level = 1
    elif trend_3h < 0 and trend_6h > 0 and trend_12h > 0:
        trend_summary = "Short-term drop in a rising trend — weather likely stabilizing after a dip."
        warning_level = 2
    elif trend_3h > 0 and trend_6h < 0 and trend_12h < 0:
        trend_summary = (
            "Short-term rise in a falling pattern — possible temporary improvement."
        )
        warning_level = 3
    elif -0.1 < trend_3h < 0.1 and -0.1 < trend_6h < 0.1 and -0.1 < trend_12h < 0.1:
        trend_summary = "Pressure is steady across all windows — stable conditions."
        warning_level = 2 if anomaly < -2 else 1
    else:
        trend_summary = "Mixed pressure trends — potential instability or transition."
        warning_level = 3 if anomaly < -2 else 2

    if short:
        # Short summary, under 255 characters
        return (
            f"{current_pressure:.1f} hPa ({anomaly:+.1f} vs norm) — "
            f"{trend_labels['3h']}/{trend_labels['6h']}/{trend_labels['12h']} — "
            f"{trend_summary} [Level {warning_level}/5]"
        )[:255]

    # Full forecast
    # Compose result
    forecast = (
        f"🧭 Current pressure: {current_pressure:.1f} hPa\n"
        f"📊 Pressure vs {region.title()} {month_name} normal ({normal} hPa): {anomaly:+.1f} hPa\n"
        f"🌀 Pressure context: {pressure_context}\n\n"
        f"📉 3h trend: {trend_labels['3h']} ({trend_3h:+.2f} hPa/hr)\n"
        f"📉 6h trend: {trend_labels['6h']} ({trend_6h:+.2f} hPa/hr)\n"
        f"📉 12h trend: {trend_labels['12h']} ({trend_12h:+.2f} hPa/hr)\n\n"
        f"🗺️ Forecast: {trend_summary}\n"
        f"⚠️ Warning Level: {warning_level}/5"
    )

    return forecast


async def get_trend(hass, entity_id, trend_duration):
    """Fetches historical pressure data, analyzing strongest rising or falling trend."""

    # Set the maximum deviation to switch from straight line analysis to U-shaped analysis
    # If the model detects U-curves too often, try increasing the threshold (e.g., avg_deviation > 2.0).
    # If it sticks to straight-line too much, decrease it slightly (e.g., avg_deviation > 1.0).
    MAX_DEVIATION = 1.5

    # Fixed interval of 15 minutes, 12 samples over 3 hours
    hours_to_read = safe_float(trend_duration)
    time_interval_minutes = 15
    num_intervals = (60 / time_interval_minutes) * hours_to_read

    # Get current time & calculate start time
    end_time = dt_util.utcnow()
    start_time = end_time - timedelta(hours=hours_to_read)

    # Fetch recorded history from Home Assistant
    history_data = await hass.async_add_executor_job(
        history.get_significant_states,
        hass,
        start_time,
        end_time,
        [entity_id],
        None,
        False,
        False,
        False,
    )

    if not history_data or entity_id not in history_data:
        _LOGGER.debug(
            f"⚠️ No history data available for {entity_id}. Using current state instead."
        )
        return "learning", "", "", 0, "", 0  # No data at all, return steady trend

    _LOGGER.debug(f"History array: {history_data}")

    # Ensure data is sorted in time order (oldest → newest)
    data_points = sorted(history_data[entity_id], key=lambda state: state.last_changed)

    pressure_values = []
    timestamps = []
    last_used_time = None

    # Select one reading per interval
    for state in data_points:
        rounded_time = state.last_changed.replace(
            minute=(state.last_changed.minute // time_interval_minutes)
            * time_interval_minutes,
            second=0,
            microsecond=0,
        )

        if last_used_time is None or rounded_time > last_used_time:
            pressure_values.append(safe_float(state.state))
            timestamps.append(rounded_time.timestamp())  # Store time in seconds
            last_used_time = rounded_time

        if len(pressure_values) >= num_intervals:
            break

    if len(pressure_values) < 2:
        return "learning", "", "", 0, "", 0  # No data at all, return steady trend

    _LOGGER.debug(f"DPT: pressure values {len(pressure_values)}")
    _LOGGER.debug(f"Pressure values array: {pressure_values}")
    _LOGGER.debug(f"Timestamp array: {timestamps}")

    # **Straight-Line Method (Linear Regression)**
    x = np.array(timestamps) - timestamps[0]  # Convert timestamps to relative time
    y = np.array(pressure_values)

    # Fit a straight line (1st degree polynomial)
    slope, intercept = np.polyfit(x, y, 1)

    # Calculate how well this straight-line fits the actual data
    fitted_y = slope * x + intercept
    deviations = np.abs(y - fitted_y)  # Absolute deviations from the fitted line
    avg_deviation = np.mean(deviations)  # Mean deviation

    _LOGGER.debug(f"DPT: Straight-line slope: {slope}, Avg deviation: {avg_deviation}")

    # **Decide if we switch to U-curve detection**
    # If deviations are large, fall back to U-curve method
    if avg_deviation > MAX_DEVIATION:  # Adjust this threshold as needed
        _LOGGER.debug(
            "DPT: Deviation from straight-line too large. Switching to U-curve analysis."
        )

        # **U-curve Method**
        min_pressure = min(pressure_values)
        max_pressure = max(pressure_values)
        min_index = pressure_values.index(min_pressure)
        max_index = pressure_values.index(max_pressure)

        last_pressure = pressure_values[-1]  # Compare to latest reading

        time_to_min = (len(pressure_values) - min_index) * (
            time_interval_minutes / 60
        )  # Convert to hours
        time_to_max = (len(pressure_values) - max_index) * (
            time_interval_minutes / 60
        )  # Convert to hours

        slope_to_min = (
            (last_pressure - min_pressure) / time_to_min if time_to_min > 0 else 0
        )
        slope_to_max = (
            (last_pressure - max_pressure) / time_to_max if time_to_max > 0 else 0
        )

        slope = slope_to_min if abs(slope_to_min) > abs(slope_to_max) else slope_to_max
    else:
        _LOGGER.debug(
            f"DPT2: Straight-line slope: {slope}, Avg deviation: {avg_deviation}"
        )

        # **Use Straight-Line Slope as Trend**
        # Convert slope to hPa per hour
        slope = slope * (3600)

    return slope
