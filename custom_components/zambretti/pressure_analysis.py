from datetime import timedelta
import numpy as np

from homeassistant.components.recorder import history
from homeassistant.util import dt as dt_util
from .helpers import safe_float

import logging
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)  # Or use logging.INFO for less verbosity


async def determine_pressure_trend(hass, entity_id, pressure_history_hours):
    """Fetches historical pressure data, analyzing strongest rising or falling trend."""

    # Set the maximum deviation to switch from straight line analysis to U-shaped analysis
    # If the model detects U-curves too often, try increasing the threshold (e.g., avg_deviation > 2.0).
    # If it sticks to straight-line too much, decrease it slightly (e.g., avg_deviation > 1.0).
    MAX_DEVIATION = 1.5


    # Fixed interval of 15 minutes, 12 samples over 3 hours
    hours_to_read = safe_float(pressure_history_hours)
#    pressure_history_hours = 3 if pressure_history_hours == 0 else safe_float(pressure_history_hours)
    time_interval_minutes = 15  
    num_intervals = (60 / time_interval_minutes) * hours_to_read

    # Get current time & calculate start time
    end_time = dt_util.utcnow()
    start_time = end_time - timedelta(hours=hours_to_read)

    # Fetch recorded history from Home Assistant
    history_data = await hass.async_add_executor_job(
        history.get_significant_states, hass, start_time, end_time, [entity_id], None, False, False, False
    )

    if not history_data or entity_id not in history_data:
        _LOGGER.debug(f"⚠️ No history data available for {entity_id}. Using current state instead.")
        current_state = hass.states.get(entity_id)
        if current_state:
            return "learning", safe_float(current_state.state), 0
        return "steady", 0, 0  # No data at all, return steady trend

    _LOGGER.debug(f"History array: {history_data}")

    # Ensure data is sorted in time order (oldest → newest)
    data_points = sorted(history_data[entity_id], key=lambda state: state.last_changed)

    pressure_values = []
    timestamps = []
    last_used_time = None

    # Select one reading per interval
    for state in data_points:
        rounded_time = state.last_changed.replace(
            minute=(state.last_changed.minute // time_interval_minutes) * time_interval_minutes, 
            second=0, microsecond=0
        )

        if last_used_time is None or rounded_time > last_used_time:
            pressure_values.append(safe_float(state.state))
            timestamps.append(rounded_time.timestamp())  # Store time in seconds
            last_used_time = rounded_time

        if len(pressure_values) >= num_intervals:
            break

    if len(pressure_values) < 2:
        return "learning", pressure_values[0], 1
    
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
        _LOGGER.debug("DPT: Deviation from straight-line too large. Switching to U-curve analysis.")
        method_used = "U-curve"
        
        # **U-curve Method**
        min_pressure = min(pressure_values)
        max_pressure = max(pressure_values)
        min_index = pressure_values.index(min_pressure)
        max_index = pressure_values.index(max_pressure)

        first_pressure = pressure_values[0]
        last_pressure = pressure_values[-1]  # Compare to latest reading

        time_to_min = (len(pressure_values) - min_index) * (time_interval_minutes / 60)  # Convert to hours
        time_to_max = (len(pressure_values) - max_index) * (time_interval_minutes / 60)  # Convert to hours

        slope_to_min = (last_pressure - min_pressure) / time_to_min if time_to_min > 0 else 0
        slope_to_max = (last_pressure - max_pressure) / time_to_max if time_to_max > 0 else 0

        slope = slope_to_min if abs(slope_to_min) > abs(slope_to_max) else slope_to_max
    else:
        _LOGGER.debug(f"DPT2: Straight-line slope: {slope}, Avg deviation: {avg_deviation}")

        # **Use Straight-Line Slope as Trend**
        method_used = "Straight-line"
        # Convert slope to hPa per hour
        slope = slope * (3600)  
        
    # Determine the trend, looking at the slope
    if slope >= 2.0:
        trend = "rising_fast"
    elif slope >= 0.5:
        trend = "rising"
    elif slope > -0.5:
        trend = "steady"
    elif slope > -2.0:
        trend = "falling"
    elif slope > -4.0:
        trend = "falling_fast"
    else:
        trend = "plummeting"        

    # Create the pressure forecast
    d_trend = trend.replace("_", " ").title()
    plus_minus = "±"
    if round(slope, 1) > 0:
        plus_minus = "+"
    elif round(slope, 2) < 0:
        plus_minus = "-"
    
    analysis = f"{d_trend} pressure, {plus_minus}{abs(round(slope,1))}/hr"

    return trend, slope, analysis, len(history_data[entity_id]), method_used, avg_deviation     
 