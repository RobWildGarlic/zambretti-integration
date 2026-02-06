import collections
import logging
import statistics
from datetime import timedelta

from homeassistant.components.recorder import history
from homeassistant.util import dt as dt_util

from .helpers import safe_float

_LOGGER = logging.getLogger(__name__)


def wind_degrees_to_text(degrees):
    """Convert wind direction in degrees to a compass direction (e.g., N, SW)."""
    directions = [
        "N",
        "N-NE",
        "NE",
        "E-NE",
        "E",
        "E-SE",
        "SE",
        "S-SE",
        "S",
        "S-SW",
        "SW",
        "W-SW",
        "W",
        "W-NW",
        "NW",
        "N-NW",
    ]
    if degrees is None:
        return "Unknown"
    index = round(degrees / 22.5) % 16
    return directions[index]


async def calculate_most_frequent_wind_direction(hass, entity_id):
    """Fetch wind direction history and determine the most frequent direction."""

    # Get wind history for the last 1 hour
    # ✅ Ensure time is always in UTC
    start_time = dt_util.utcnow() - timedelta(minutes=10)
    end_time = dt_util.utcnow()

    # Fetch recorded history from the HA database
    history_data = {}
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
    try:
        if len(history_data) > 0:
            _LOGGER.debug(
                f"✅ Found history for {entity_id}, total records: {len(history_data[entity_id])}"
            )
        else:
            _LOGGER.debug(f"⚠️ No history for {entity_id}.")
    except ValueError:
        _LOGGER.debug(f"⚠️ No history for {entity_id}. Except.")

    wind_directions = []

    # Extract wind direction values
    wind_directions = []
    for state in history_data[entity_id]:
        wind_value = safe_float(state.state)
        if wind_value is not None:
            wind_directions.append(wind_degrees_to_text(wind_value))
        else:
            _LOGGER.debug(f"⚠️ Skipping invalid wind value: {wind_value}")

    # If no history yet, fall back to current sensor state
    if not wind_directions:
        current_state = hass.states.get(entity_id)
        if current_state:
            wind_value = safe_float(current_state.state)
            if wind_value is not None:
                return wind_degrees_to_text(wind_value), 1
        return (
            "Error: Wind direction not available.",
            0,
        )  # If even the current state is missing

    # Find the most frequent wind direction
    return collections.Counter(wind_directions).most_common(1)[0][0], len(
        history_data[entity_id]
    )


async def determine_wind_speed(hass, entity_id):
    """Fetches historical wind speed to determine average."""

    # ✅ Ensure time is always in UTC
    start_time = dt_util.utcnow() - timedelta(minutes=10)
    end_time = dt_util.utcnow()

    # Fetch wind speed history from HA database
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
        current_state = hass.states.get(entity_id)
        if current_state:
            return safe_float(
                current_state.state
            ), 1  # Returning 1 as a single data point
        return 0, 0  # No valid data available

    # Extract wind speed values
    wind_speed_values = [
        safe_float(state.state) for state in history_data.get(entity_id, [])
    ]
    # ✅ Calculate the average wind speed
    average_wind_speed = statistics.mean(wind_speed_values) if wind_speed_values else 0

    _LOGGER.debug(
        f"✅ Calculated average wind speed: {average_wind_speed} knots over {len(wind_speed_values)} records."
    )

    return average_wind_speed, len(history_data[entity_id])


def determine_wind_direction(wind_direction, pressure_trend):
    """Determines the future wind direction based on current wind direction and pressure trend."""

    _LOGGER.debug(
        f"🔄 Estimating wind direction shift from {wind_direction} with trend: {pressure_trend}"
    )

    # Define the wind direction order in a 16-point compass rose
    compass_directions = [
        "N",
        "N-NE",
        "NE",
        "E-NE",
        "E",
        "E-SE",
        "SE",
        "S-SE",
        "S",
        "S-SW",
        "SW",
        "W-SW",
        "W",
        "W-NW",
        "NW",
        "N-NW",
    ]

    # **Mapping for cardinal direction conversion**
    veering_map = {  # Moving clockwise
        "N": "E",
        "N-NE": "E",
        "NE": "E",
        "E-NE": "E",
        "E": "S",
        "E-SE": "S",
        "SE": "S",
        "S-SE": "S",
        "S": "W",
        "S-SW": "W",
        "SW": "W",
        "W-SW": "W",
        "W": "N",
        "W-NW": "N",
        "NW": "N",
        "N-NW": "N",
    }

    backing_map = {  # Moving counterclockwise
        "N": "W",
        "N-NE": "N",
        "NE": "N",
        "E-NE": "N",
        "E": "N",
        "E-SE": "E",
        "SE": "E",
        "S-SE": "E",
        "S": "E",
        "S-SW": "S",
        "SW": "S",
        "W-SW": "S",
        "W": "S",
        "W-NW": "W",
        "NW": "W",
        "N-NW": "W",
    }

    # Check if wind_direction is valid
    if wind_direction not in compass_directions:
        return "Invalid wind direction"

    # **Determine wind change type based on pressure trend**
    wind_change = "steady"
    wind_change_speed = ""

    if pressure_trend in ["plummeting", "falling_fast"]:
        wind_change = "backing"
        wind_change_speed = "fast"
    elif pressure_trend in ["rising_fast"]:
        wind_change = "veering"
        wind_change_speed = "fast"
    elif pressure_trend == "rising":
        wind_change = "veering"
    elif pressure_trend == "falling":
        wind_change = "backing"

    # **Determine new wind direction, construct estimated sind direction text**
    if wind_change == "veering":
        future_direction_cardinal = veering_map[wind_direction]
        estimated_wind_direction = f"{wind_direction} {wind_change} towards {future_direction_cardinal} {wind_change_speed}".strip()
    elif wind_change == "backing":
        future_direction_cardinal = backing_map[wind_direction]
        estimated_wind_direction = f"{wind_direction} {wind_change} towards {future_direction_cardinal} {wind_change_speed}".strip()
    else:
        future_direction_cardinal = wind_direction  # No change
        estimated_wind_direction = f"{wind_direction} {wind_change}".strip()

    _LOGGER.debug(f"✅ Estimated wind change: {estimated_wind_direction}")

    return estimated_wind_direction
