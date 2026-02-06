# custom_components/zambretti/ai_prompt.py

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

# Recorder history function (sync) - run via hass.async_add_executor_job
from homeassistant.components.recorder.history import state_changes_during_period
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

DEFAULT_HISTORY_HOURS = 24
DEFAULT_SAMPLE_MINUTES = 60  # hourly samples, keeps attribute size reasonable


def _safe_float(v: Any) -> float | None:
    try:
        if v is None:
            return None
        s = str(v).strip()
        if s in ("unknown", "unavailable", ""):
            return None
        return float(s)
    except Exception:
        return None


def _state_str(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    if s in ("unknown", "unavailable", ""):
        return None
    return s


def _iso(dt: datetime) -> str:
    # Always timezone-aware in HA
    return dt.isoformat(timespec="seconds")


def _history_sync(
    hass: HomeAssistant,
    entity_id: str,
    start: datetime,
    end: datetime,
) -> list[Any]:
    """Fetch raw state history (sync). Returns list of State objects."""
    try:
        # state_changes_during_period returns dict: { entity_id: [State, State, ...] }
        data = state_changes_during_period(hass, start, end, entity_id=entity_id)
        return data.get(entity_id, []) if data else []
    except Exception as e:
        _LOGGER.debug("AI prompt: history fetch failed for %s: %s", entity_id, e)
        return []


def _build_hourly_samples(
    raw_states: list[Any],
    start: datetime,
    end: datetime,
    sample_minutes: int,
    numeric: bool,
) -> list[dict[str, Any]]:
    """
    Downsample raw recorder states into regular samples.
    Strategy: for each sample time, pick the latest state at or before that time.
    """
    if not raw_states:
        return []

    # Ensure states sorted by last_updated (fallback to last_changed)
    def _state_time(st) -> datetime:
        return st.last_updated or st.last_changed

    states_sorted = sorted(raw_states, key=_state_time)

    samples: list[dict[str, Any]] = []
    t = start

    idx = 0
    last_value: Any | None = None
    last_time: datetime | None = None

    # Move idx forward while state_time <= t, so last_value is "latest at or before t"
    while t <= end:
        while idx < len(states_sorted) and _state_time(states_sorted[idx]) <= t:
            st = states_sorted[idx]
            last_value = st.state
            last_time = _state_time(st)
            idx += 1

        if last_value is not None and last_time is not None:
            if numeric:
                fv = _safe_float(last_value)
                if fv is not None:
                    samples.append({"t": _iso(t), "v": fv})
            else:
                sv = _state_str(last_value)
                if sv is not None:
                    samples.append({"t": _iso(t), "v": sv})

        t += timedelta(minutes=sample_minutes)

    return samples


def _fmt_series(series: list[dict[str, Any]], unit: str = "") -> str:
    """Format a series for inclusion in the prompt."""
    if not series:
        return "- (no data)\n"

    lines = []
    for p in series:
        v = p["v"]
        v_str = f"{v:.1f}" if isinstance(v, float) else str(v)
        lines.append(f"- {p['t']}: {v_str}{unit}")
    return "\n".join(lines) + "\n"


def _get_attr(attrs: dict[str, Any], key: str) -> Any:
    return attrs.get(key)


def _human_time(dt: datetime) -> str:
    now = dt_util.now()

    # Round to nearest 5 minutes for nicer text
    minute = int(round(dt.minute / 5) * 5)
    if minute == 60:
        dt = dt.replace(hour=(dt.hour + 1) % 24, minute=0)
    else:
        dt = dt.replace(minute=minute)

    today = now.date()
    d = dt.date()

    # Time string
    t = dt.strftime("%H:%M")
    # Or if you prefer English words:
    # t = dt.strftime("%-I:%M %p")  # "8:00 PM" (platform dependent)

    if d == today:
        return f"{t} today"
    elif d == today - timedelta(days=1):
        return f"{t} yesterday"
    elif d == today - timedelta(days=2):
        return f"{t} day before yesterday"
    else:
        return dt.strftime("%Y-%m-%d %H:%M")


async def build_ai_prompt(
    hass: HomeAssistant,
    *,
    # entity_ids for history
    pressure_entity_id: str | None,
    temperature_entity_id: str | None,
    wind_speed_entity_id: str | None,
    wind_direction_entity_id: str | None,
    # current zambretti attributes (already computed in sensor.py)
    z_attrs: dict[str, Any],
    # prompt settings
    history_hours: int = DEFAULT_HISTORY_HOURS,
    sample_minutes: int = DEFAULT_SAMPLE_MINUTES,
) -> dict[str, Any]:
    """
    Returns:
      {
        "prompt": "<string>",
        "history": {
          "pressure_hpa": [ {"t": "...", "v": 1012.3}, ... ],
          "temperature_c": [ ... ],
          "wind_speed_kn": [ ... ],
          "wind_direction": [ {"t": "...", "v": "270"} or 270.0, ... ],
          "meta": {"hours": 24, "sample_minutes": 60}
        }
      }
    """
    now = dt_util.now()
    start = now - timedelta(hours=history_hours)

    # Fetch histories (sync recorder call -> executor)
    async def fetch(entity_id: str) -> list[Any]:
        return await hass.async_add_executor_job(
            _history_sync, hass, entity_id, start, now
        )

    raw_pressure = await fetch(pressure_entity_id) if pressure_entity_id else []
    raw_temp = await fetch(temperature_entity_id) if temperature_entity_id else []
    raw_ws = await fetch(wind_speed_entity_id) if wind_speed_entity_id else []
    raw_wd = await fetch(wind_direction_entity_id) if wind_direction_entity_id else []

    # Build sampled series
    pressure_series = _build_hourly_samples(
        raw_pressure, start, now, sample_minutes, numeric=True
    )
    temp_series = _build_hourly_samples(
        raw_temp, start, now, sample_minutes, numeric=True
    )
    ws_series = _build_hourly_samples(raw_ws, start, now, sample_minutes, numeric=True)

    # Wind direction may be numeric degrees or cardinal; keep as string but allow numeric if it parses.
    wd_series_raw = _build_hourly_samples(
        raw_wd, start, now, sample_minutes, numeric=False
    )
    # try to coerce v into float if it looks numeric, else keep string
    wd_series: list[dict[str, Any]] = []
    for p in wd_series_raw:
        fv = _safe_float(p["v"])
        wd_series.append({"t": p["t"], "v": fv if fv is not None else p["v"]})

    history = {
        "pressure_hpa": pressure_series,
        "temperature_c": temp_series,
        "wind_speed_kn": ws_series,
        "wind_direction": wd_series,
        "meta": {"hours": history_hours, "sample_minutes": sample_minutes},
    }

    # Pull the main “current/derived” values from z_attrs (best effort; missing is OK)
    region = _get_attr(z_attrs, "region")

    prompt = f"""## Context
- Region: {region}
- Generated at: {_human_time(now)}

## Current observations (from Home Assistant)
- Pressure (hPa): {_get_attr(z_attrs, "pressure")}
- Pressure trend: {_get_attr(z_attrs, "pressure_trend")}
- Pressure change per hour (hPa/h): {_get_attr(z_attrs, "pressure_move_per_hour")}
- Wind speed (kn): {_get_attr(z_attrs, "wind_speed")}
- Wind direction: {_get_attr(z_attrs, "wind_direction")}
- Wind direction change: {_get_attr(z_attrs, "wind_direction_change")}
- Temperature (°C): {_get_attr(z_attrs, "sensor_temperature")}
- Humidity (%): {_get_attr(z_attrs, "sensor_humidity")}
- Dew point: {_get_attr(z_attrs, "dewpoint")}

## Fog indicators
- Fog chance: {_get_attr(z_attrs, "fog_chance")} ({_get_attr(z_attrs, "fog_chance_pct")}%)
- Temp difference for fog: {_get_attr(z_attrs, "temp_diff_fog")}

## Low-pressure estimator (if available)
- Low direction: {_get_attr(z_attrs, "low_direction")} (deg: {_get_attr(z_attrs, "low_direction_deg")})
- Low distance class: {_get_attr(z_attrs, "low_distance_class")}
- Low distance km range: {_get_attr(z_attrs, "low_distance_km_range")}
- Low wind trend class: {_get_attr(z_attrs, "low_wind_trend_class")}
- Low wind delta (kn): {_get_attr(z_attrs, "low_wind_trend_delta_kn")}
- Low wind direction delta (deg): {_get_attr(z_attrs, "low_wind_dir_delta_deg")}
- Low weather trend: {_get_attr(z_attrs, "low_weather_trend")}
- Time to impact: {_get_attr(z_attrs, "low_time_to_impact")} (range: {_get_attr(z_attrs, "low_time_to_impact_range")})
- Wind rotation likely: {_get_attr(z_attrs, "low_wind_rotation_likely")}
- Frontal zone: {_get_attr(z_attrs, "low_frontal_zone")}


## 24h history (hourly samples)
### Pressure (hPa)
{_fmt_series(pressure_series, " hPa")}
### Temperature (°C)
{_fmt_series(temp_series, " °C")}
### Wind speed (kn)
{_fmt_series(ws_series, " kn")}
### Wind direction
{_fmt_series(wd_series, "")}

Now produce the forecast.
"""

    return {"prompt": prompt, "history": history}
