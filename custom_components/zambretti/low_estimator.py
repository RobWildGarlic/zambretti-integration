"""
low_estimator.py  (Zambretti custom integration helper)

What this module does
---------------------
It estimates, from *local* measurements, several useful "synoptic" hints:

Core (already present)
- low direction: N/NE/E/...
- low distance class: Far/Distant/Approaching/Near/Very near/Imminent (+ rough km range)
- wind trend: Increasing/Decreasing/Stable (+ "a lot")
- confidence: low/medium/high (conservative)

Additional derived signals (added now)
1) Weather trend index:
   Improving / Stable / Deteriorating / Rapidly deteriorating
2) Time-to-impact class:
   >24h / 12–24h / 6–12h / 3–6h / <3h  (rough, based on distance class)
3) Wind rotation expectation:
   Backing likely / Veering likely / Uncertain
   (Uses wind direction history to see whether wind is currently backing/veering.)
5) Front proximity heuristic:
   frontal_zone: True/False (very simple heuristic)
6) Anchoring risk:
   Safe / Caution / Unsafe

Design choice (per your request)
--------------------------------
This module fetches its *own* history from Home Assistant's recorder.
That keeps sensor.py simple (orchestration only).

Assumptions
-----------
- Northern Hemisphere.
- wind direction is meteorological "FROM" degrees (0=N, 90=E, etc.).
- These are *heuristics* to support situational awareness, not precise forecasting.

How to call from sensor.py
--------------------------
    from .low_estimator import async_estimate_low_properties

    low = await async_estimate_low_properties(
        hass=self.hass,
        wind_from_entity_id=self.wind_direction_sensor,
        wind_speed_entity_id=self.wind_speed_sensor,
        pressure_entity_id=self.pressure_sensor,
        # optional overrides:
        wind_speed_history_minutes=90,
        wind_dir_history_minutes=120,
        pressure_history_hours=12,
        pressure_slope_window_hours=3,
    )

Then publish attributes using low.<field> (see dataclass below).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from math import isnan
from typing import Any, Optional, Tuple, List


# ---------------------------------------------------------------------
# Small utility helpers
# ---------------------------------------------------------------------

def _safe_float(x: Any) -> Optional[float]:
    """Convert x to float, returning None for None/NaN/invalid."""
    try:
        if x is None:
            return None
        v = float(x)
        if isnan(v):
            return None
        return v
    except (TypeError, ValueError):
        return None


def _clamp_deg(deg: float) -> float:
    """Normalize degrees into [0, 360)."""
    return deg % 360.0


def _compass_8(deg: float) -> str:
    """Convert degrees to 8-point compass label."""
    deg = _clamp_deg(deg)
    idx = int((deg + 22.5) // 45) % 8
    return ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][idx]


def _circular_delta_deg(start_deg: float, end_deg: float) -> float:
    """
    Smallest signed angular change from start -> end in degrees.

    Returns value in [-180, 180).
    Positive means clockwise rotation (veering in NH terms).
    Negative means counter-clockwise rotation (backing).
    """
    a = _clamp_deg(start_deg)
    b = _clamp_deg(end_deg)
    d = (b - a + 180.0) % 360.0 - 180.0
    return d


def _wind_delta_knots(history: Any) -> Optional[float]:
    """Simple delta (last - first) from a history sequence. Returns None if too short."""
    try:
        vals: List[float] = []
        for v in history or []:
            fv = _safe_float(v)
            if fv is not None:
                vals.append(fv)
        if len(vals) < 2:
            return None
        return vals[-1] - vals[0]
    except TypeError:
        # history not iterable
        return None


# ---------------------------------------------------------------------
# Public output
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class LowEstimate:
    # Core
    low_bearing_deg: float
    low_bearing_compass: str
    distance_class: str
    distance_km_range: str
    wind_trend: str
    wind_delta_kn: Optional[float]
    confidence: str
    hemisphere: str

    # Expose the computed pressure slope we used (useful for debugging/analytics)
    pressure_slope_hpa_per_hr: Optional[float]

    # Added derived signals
    weather_trend: str
    time_to_impact: str
    time_to_impact_range: str
    wind_rotation_likely: str
    wind_dir_delta_deg: Optional[float]
    frontal_zone: bool
    anchoring_risk: str
    # Relative position/movement inference (single-station; heuristic)
    low_relative_position: str  # West / East / North-South / Unknown
    low_movement: str  # Approaching / Passing / Receding / Unknown
    impact_window_status: str  # Future / Now / Passed / Unknown

    # Human-readable explanation
    summary: str


# ---------------------------------------------------------------------
# Pure estimator (no HA dependencies)
# ---------------------------------------------------------------------

_DISTANCE_ORDER = ["Far", "Distant", "Approaching", "Near", "Very near", "Imminent"]
_DISTANCE_RANGE = {
    "Far": "1000–2000 km",
    "Distant": "700–1000 km",
    "Approaching": "400–700 km",
    "Near": "200–400 km",
    "Very near": "80–200 km",
    "Imminent": "0–80 km",
}

_IMPACT_MAP = {
    "Far": (">24h", "> 24 hours"),
    "Distant": ("12–24h", "12–24 hours"),
    "Approaching": ("6–12h", "6–12 hours"),
    "Near": ("3–6h", "3–6 hours"),
    "Very near": ("<3h", "< 3 hours"),
    "Imminent": ("<3h", "< 3 hours"),
}


def _shift_closer(distance_class: str, *, steps: int = 1) -> str:
    """Move the distance_class closer by N steps in the ordering."""
    try:
        i = _DISTANCE_ORDER.index(distance_class)
    except ValueError:
        return distance_class
    j = min(len(_DISTANCE_ORDER) - 1, i + steps)
    return _DISTANCE_ORDER[j]


def _combine_confidence(*parts: str) -> str:
    """
    Conservative combination: overall confidence is the *lowest* of the parts.
    This prevents us from claiming "high" if one input is weak/missing.
    """
    score = {"low": 0, "medium": 1, "high": 2}
    inv = {0: "low", 1: "medium", 2: "high"}
    m = min(score.get(p, 0) for p in parts)
    return inv[m]


def _confidence_text(conf: str) -> str:
    """Map confidence token to a human-friendly phrase."""
    return {
        "high": "high confidence",
        "medium": "medium confidence",
        "low": "low confidence",
    }.get(conf, conf)


def build_low_summary(low: "LowEstimate") -> str:
    """
    Create a human-readable explanation string for dashboards/notifications.

    Kept intentionally compact so it fits in UI cards/chips while still being useful.
    """
    # Direction + distance
    if low.distance_class and low.distance_class != "Unknown":
        dist = f"{low.distance_class.lower()} ({low.distance_km_range})"
    else:
        dist = "unknown distance"

    direction = f"{low.low_bearing_compass} ({low.low_bearing_deg:.0f}°)" if low.low_bearing_compass else "unknown direction"
    if getattr(low, 'impact_window_status', None) == 'Passed':
        impact = 'already passed'
    elif getattr(low, 'impact_window_status', None) == 'Now':
        impact = 'now / imminent'
    elif getattr(low, 'time_to_impact_range', None):
        impact = low.time_to_impact_range
    else:
        impact = 'unknown time window'
    conf = _confidence_text(low.confidence)

    # Wind line
    if low.wind_delta_kn is None:
        wind_line = "Wind trend unknown."
    else:
        sign = "+" if low.wind_delta_kn >= 0 else ""
        wind_line = f"Wind {low.wind_trend.lower()} (Δ {sign}{low.wind_delta_kn:.1f} kn)."

    # Rotation / front / anchor
    rot = ""
    if low.wind_rotation_likely and low.wind_rotation_likely not in ("Uncertain", "Unknown"):
        rot = f" Rotation: {low.wind_rotation_likely}."
    elif low.wind_rotation_likely:
        rot = " Rotation: uncertain."

    front = " Frontal zone likely." if low.frontal_zone else ""
    anchor = f" Anchor: {low.anchoring_risk}." if low.anchoring_risk else ""

    return (
        f"Low to {direction}, {dist}. "
        f"Outlook: {low.weather_trend}. "
        f"Impact window: {impact} ({conf}). "
        f"{wind_line}{rot}{front}{anchor}"
    ).strip()


def _derive_weather_trend(distance_class: str, wind_trend: str) -> str:
    """
    1) Weather trend index.
    Simple mapping plus wind-trend modifier.
    """
    base = {
        "Far": "Stable",
        "Distant": "Stable",
        "Approaching": "Deteriorating",
        "Near": "Deteriorating",
        "Very near": "Rapidly deteriorating",
        "Imminent": "Rapidly deteriorating",
    }.get(distance_class, "Stable")

    # If wind is clearly easing while the system is not near, treat as improving.
    if "Decreased" in wind_trend and distance_class in ("Far", "Distant", "Approaching"):
        return "Improving"

    # If wind is ramping hard, upgrade one step.
    if "Increasing a lot" in wind_trend:
        if base == "Stable":
            return "Deteriorating"
        if base == "Deteriorating":
            return "Rapidly deteriorating"

    return base


def _derive_wind_rotation_likely(distance_class: str, wind_dir_delta_deg: Optional[float]) -> str:
    """
    Wind direction change (veer/back) from recent history.

    We separate *observed* rotation from a statement about whether it is "likely" to continue:
      - If rotation is tiny: say "No significant change".
      - If rotation is modest: say "Slight veering/backing".
      - If rotation is strong:
          * when a low is near-ish -> "Veering/Backing likely"
          * otherwise -> "Veering/Backing (observed)" (no claim about continuation)
    """
    if wind_dir_delta_deg is None:
        return "Unknown"

    d = float(wind_dir_delta_deg)

    # Tiny/noisy range
    if abs(d) < 3.0:
        return "No significant change"

    # Modest rotation: report it, but avoid overclaiming
    if abs(d) < 10.0:
        return "Slight veering" if d > 0 else "Slight backing"

    nearish = distance_class in ("Approaching", "Near", "Very near", "Imminent")
    if d > 0:
        return "Veering likely" if nearish else "Veering (observed)"
    return "Backing likely" if nearish else "Backing (observed)"



def _derive_frontal_zone(distance_class: str, pressure_slope_hpa_per_hr: Optional[float], wind_trend: str) -> bool:
    """
    5) Front proximity heuristic.
    Very simple: near-ish low + notable pressure fall + wind increasing.
    """
    if distance_class not in ("Near", "Very near", "Imminent"):
        return False
    if pressure_slope_hpa_per_hr is None:
        return False
    # notable fall rate (hPa/hr)
    if pressure_slope_hpa_per_hr > -0.5:
        return False
    if "Increasing" not in wind_trend:
        return False
    return True


def _derive_anchoring_risk(distance_class: str, wind_trend: str) -> str:
    """
    6) Anchoring risk.
    Conservative: if low is near-ish AND wind rising -> unsafe.
    """
    if distance_class in ("Very near", "Imminent"):
        return "Unsafe"
    if distance_class == "Near":
        return "Unsafe" if "Increasing" in wind_trend else "Caution"
    if distance_class == "Approaching":
        return "Caution" if ("Increasing" in wind_trend or "Stable" in wind_trend) else "Safe"
    return "Safe"



def _derive_relative_position_and_movement(
    low_compass_8: str,
    pressure_slope_hpa_per_hr: Optional[float],
    distance_class: str,
    wind_trend: str,
) -> Tuple[str, str, str]:
    """
    Infer where the low is relative to us (roughly West/East/etc) and whether it is
    approaching / passing / receding.

    IMPORTANT: this is *single-station* inference. We therefore keep it simple and
    consistent with the strongest local signals:

      - Pressure FALLING  -> approaching (impact in the future), unless we're already very near a minimum.
      - Pressure RISING   -> receding (impact passed), even if the low is already far away.
      - Pressure near-flat and near-ish distance -> passing/overhead (impact now).

    We still report the Buys-Ballot-derived sector ("East"/"West"/...) because it's useful context,
    but we do NOT gate movement on distance (that caused false "unknown" when pressure was
    already rising slowly).
    """
    comp = str(low_compass_8 or "").upper().strip()
    ps = pressure_slope_hpa_per_hr

    # Relative sector (8-point compass)
    COMPASS_NAMES = {
        "N": "North",
        "NE": "North-East",
        "E": "East",
        "SE": "South-East",
        "S": "South",
        "SW": "South-West",
        "W": "West",
        "NW": "North-West",
    }
    pos = COMPASS_NAMES.get(comp, "Unknown")
    
    if ps is None:
        return pos, "Unknown", "Unknown"

    # Tuned thresholds for pressure slope (hPa/hr)
    # These are intentionally low because marine barometers often show smaller residual trends
    # well after the main passage.
    FALLING = -0.05   # falling at least slightly
    RISING = +0.05    # rising at least slightly
    FLAT = 0.03       # near-flat band around zero
    NEARISH = distance_class in ("Near", "Very near", "Imminent")

    # Passing / overhead: near-ish AND pressure close to minimum (slope near zero)
    if NEARISH and abs(ps) <= FLAT:
        return pos, "Passing", "Now"

    # Receding: pressure rising, or strong easing winds (post-frontal signature)
    if ps >= RISING or wind_trend in ("Decreased a lot", "Decreased"):
        return pos, "Moving away", "Passed"

    # Approaching: pressure falling
    if ps <= FALLING:
        return pos, "Approaching", "Future"

    # Otherwise: weak signal
    return pos, "Unknown", "Unknown"


def estimate_low_properties(
    *,
    wind_from_deg: Any,
    pressure_slope_hpa_per_hr: Any,
    wind_speed_kn: Any = None,
    wind_speed_history_kn: Any = None,
    wind_dir_delta_deg: Any = None,
    hemisphere: str = "north",
) -> LowEstimate:
    """
    Pure heuristic estimator.

    Inputs:
      wind_from_deg: meteorological wind direction (degrees FROM which wind blows).
      pressure_slope_hpa_per_hr: pressure change rate in hPa/hour (negative means falling).
      wind_speed_kn: current wind speed in knots (optional).
      wind_speed_history_kn: sequence of historic wind speeds in knots (optional).
      wind_dir_delta_deg: signed recent wind-direction rotation in degrees (optional).
                         (+ => veering, - => backing)

    Output: LowEstimate (includes derived fields).
    """
    wdir = _safe_float(wind_from_deg)
    pslope = _safe_float(pressure_slope_hpa_per_hr)
    wspd = _safe_float(wind_speed_kn)
    wdir_delta = _safe_float(wind_dir_delta_deg)


    # ----------------------------
    # Defaults for derived fields
    # ----------------------------
    # We initialize these so the summary (and the return object) can never crash due to
    # an unassigned local variable, even if some inputs are missing.
    weather_trend = "Stable"
    time_to_impact = "Unknown"
    time_to_impact_range = "Unknown"
    wind_rotation_likely = "Uncertain"
    frontal_zone = False
    anchoring_risk = "Safe"
    low_relative_position = "Unknown"
    low_movement = "Unknown"
    impact_window_status = "Unknown"

    # ----------------------------
    # Core 1) Direction to low (NH rule of thumb)
    # ----------------------------
    if wdir is None:
        low_deg = 0.0
        low_compass = "N"
        conf_dir = "low"
    else:
        # Hemisphere matters: Buys-Ballot flips across the equator.
        # North: low ≈ wind_from + 90° ; South: low ≈ wind_from - 90°
        if str(hemisphere).lower().startswith("s"):
            low_deg = _clamp_deg(wdir - 90.0)
        else:
            low_deg = _clamp_deg(wdir + 90.0)
        low_compass = _compass_8(low_deg)
        conf_dir = "medium"

    # ----------------------------
    # Core 2) Distance class from pressure fall rate + optional wind speed
    # ----------------------------
    if pslope is None:
        distance_class = "Unknown"
        km_range = "Unknown"
        conf_dist = "low"
        fall_rate = None
    else:
        fall_rate = max(0.0, -pslope)  # hPa/hr (magnitude of fall)

        if fall_rate < 0.05:
            distance_class = "Far"
        elif fall_rate < 0.15:
            distance_class = "Distant"
        elif fall_rate < 0.35:
            distance_class = "Approaching"
        elif fall_rate < 0.70:
            distance_class = "Near"
        elif fall_rate < 1.50:
            distance_class = "Very near"
        else:
            distance_class = "Imminent"

        # Strong wind + falling pressure -> tighten/closer (nudge closer)
        if wspd is not None and fall_rate >= 0.15:
            if wspd >= 30:
                distance_class = _shift_closer(distance_class, steps=2)
            elif wspd >= 20:
                distance_class = _shift_closer(distance_class, steps=1)

        km_range = _DISTANCE_RANGE.get(distance_class, "Unknown")
        conf_dist = "medium" if fall_rate >= 0.15 else "low"

    # ----------------------------
    # Core 3) Wind trend from history (delta over window)
    # ----------------------------
    delta_kn = _wind_delta_knots(wind_speed_history_kn)
    wind_outlook = None

    if delta_kn is None:
        wind_trend = "Stable/unknown"
        conf_wind = "low"
    else:
        if delta_kn <= -5:
            wind_trend = "Decreased a lot"
        elif delta_kn <= -2:
            wind_trend = "Decreased"
        elif delta_kn < 2:
            wind_trend = "Stable"
        elif delta_kn < 5:
            wind_trend = "Increased"
        else:
            wind_trend = "Increased a lot"

        # Heuristic outlook: fast pressure fall often precedes strengthening winds.
        # Keep wind_trend as an observed (history-based) classification; expose outlook separately.
        if pslope is not None and pslope < -0.5:
            if wind_trend in ("Stable", "Stable/unknown"):
                wind_outlook = "Wind likely to increase as pressure continues to fall."
            elif wind_trend in ("Increased","Increased a lot"):
                wind_outlook = "Wind likely to increase further as pressure continues to fall."
        elif pslope is not None and pslope >= -0.5 and pslope <= 0.5:
            if delta_kn < 1:
                wind_outlook = "Wind likely to be stable."
            else:
                wind_outlook = "Wind likely to be almost stable."
        elif pslope is not None and pslope > 0.5:
            if wind_trend in ("Stable", "Stable/unknown","Decreased","Decreased a lot"):
                wind_outlook = "Wind likely to decrease as pressure continues to rise."
        else:
            wind_outlook = "Wind confusing, keep an eye out."
#        wind_outlook += f"(Pslope: {pslope}, trend: {wind_trend})."
        conf_wind = "medium"
    confidence = _combine_confidence(conf_dir, conf_dist, conf_wind)

    # ----------------------------
    # Added derived signals
    # ----------------------------
    weather_trend = _derive_weather_trend(distance_class, wind_trend)

    # Relative position / movement (accounts for the common W→E drift of lows)
    low_relative_position, low_movement, impact_window_status = _derive_relative_position_and_movement(
        low_compass, pslope, distance_class, wind_trend
    )

    # Impact window logic:
    # - If the low is receding (often already to the east + pressure rising), the impact is in the past.
    # - If we're near a passage, impact is 'now'.
    # - Otherwise fall back to distance-based timing buckets.
    if impact_window_status == "Passed":
        time_to_impact, time_to_impact_range = "Passed", "already passed"
        # If we were calling this 'deteriorating' purely from distance class, soften it.
        if weather_trend in ("Deteriorating", "Rapidly deteriorating"):
            weather_trend = "Improving"
    elif impact_window_status == "Now":
        time_to_impact, time_to_impact_range = "Now", "now / next 1–2 hours"
    else:
        impact = _IMPACT_MAP.get(distance_class)
        if impact is None:
            time_to_impact, time_to_impact_range = "Unknown", "Unknown"
        else:
            time_to_impact, time_to_impact_range = impact
    wind_rotation_likely = _derive_wind_rotation_likely(distance_class, wdir_delta)

    frontal_zone = _derive_frontal_zone(distance_class, pslope, wind_trend)
    anchoring_risk = _derive_anchoring_risk(distance_class, wind_trend)

    # Human-readable summary (used as attribute in HA)
    parts: list[str] = []

    parts.append(f"Low to the {low_relative_position.lower()} ({low_deg:.0f}°), ")
    if distance_class != "Unknown":
        parts.append(f"distance {km_range}, {low_movement.lower()}.")
#        parts.append(f"distance {distance_class.lower()} ({km_range}), {low_movement.lower()}.")
    else:
        parts.append("Distance: unknown.")

#    if low_relative_position != "Unknown" or low_movement != "Unknown":
#        parts.append(f"Relative to you: {low_relative_position.lower()}, {low_movement.lower()}.")

    # Main weather impact timing (human readable)
    if impact_window_status == "Passed":
         parts.append(
             "Main weather from this system has passed, conditions are improving."
         )
    elif impact_window_status == "Now":
            parts.append(
                "Main impact from this system is occurring now or is imminent, "
                "expect the worst conditions in the next 1–2 hours."
            )
    elif impact_window_status == "Future":
        # Distinguish near-term vs far-term using the existing time_to_impact_range
        if time_to_impact_range in ("< 3 hours", "3–6 hours", "6–12 hours"):
            parts.append(
                f"Weather is deteriorating, main impact from this system is expected within {time_to_impact_range}. "
                "Prepare for worsening conditions."
            )
        else:
            parts.append(
                "A low pressure system is present but still far away. "
                "No significant impact is expected in the next 12–24 hours."
            )
    else:
        parts.append(
            "Weather situation is unclear. Signals are mixed; monitor pressure and wind trends closely."
        )
    
    # Pressure trend
    if pslope is not None:
        if abs(pslope) < 0.10:
            parts.append("Pressure: roughly steady.")
        elif pslope < 0:
            parts.append(f"Pressure: falling ({pslope:.2f} hPa/hr).")
        else:
            parts.append(f"Pressure: rising (+{pslope:.2f} hPa/hr).")

    # Wind
    if wspd is None:
        parts.append("Current wind: unknown.")
    else:
        wind_clause = f"Current wind: {wspd:.0f} kn"
        if delta_kn is None:
            wind_clause += f" ({wind_trend.lower()})."
        else:
            wind_clause += f", {wind_trend.lower()} (Δ {'+' if delta_kn >= 0 else ''}{delta_kn:.1f} kn)."
        parts.append(wind_clause)
        parts.append(wind_outlook)

    if wind_rotation_likely:
        if wind_rotation_likely not in ("Uncertain", "Unknown"):
            parts.append(f"Likely direction change: {wind_rotation_likely.lower()}.")
        else:
            parts.append("Likely direction change: uncertain.")

    if frontal_zone:
        parts.append("Frontal zone likely.")

    if anchoring_risk:
        parts.append(f"Anchoring risk: {anchoring_risk}.")

    summary = " ".join(parts).strip()
    return LowEstimate(
        low_bearing_deg=round(low_deg, 1),
        low_bearing_compass=low_compass,
        distance_class=distance_class,
        distance_km_range=km_range,
        wind_trend=wind_trend,
        wind_delta_kn=round(delta_kn, 2) if delta_kn is not None else None,
        confidence=confidence,
        hemisphere=hemisphere,
        pressure_slope_hpa_per_hr=round(pslope, 3) if pslope is not None else None,
        weather_trend=weather_trend,
        time_to_impact=time_to_impact,
        time_to_impact_range=time_to_impact_range,
        wind_rotation_likely=wind_rotation_likely,
        wind_dir_delta_deg=round(wdir_delta, 1) if wdir_delta is not None else None,
        frontal_zone=frontal_zone,
        anchoring_risk=anchoring_risk,
        low_relative_position=low_relative_position,
        low_movement=low_movement,
        impact_window_status=impact_window_status,
        summary=summary,
    )


# ---------------------------------------------------------------------
# HA history fetching + async convenience wrapper
# ---------------------------------------------------------------------

async def async_estimate_low_properties(
    *,
    hass,
    wind_from_entity_id: str,
    wind_speed_entity_id: str,
    pressure_entity_id: str,
    wind_speed_history_minutes: int = 90,
    wind_dir_history_minutes: int = 120,
    pressure_history_hours: int = 12,
    pressure_slope_window_hours: int = 3,
    latitude: float | None = None,
) -> LowEstimate:
    """
    Fetch required data from HA recorder + current states, then run estimate_low_properties().

    Defaults are conservative and stable:
      - wind_speed_history_minutes=90: reduces gust-noise, still responsive
      - wind_dir_history_minutes=120: enough to see backing/veering without overreacting
      - pressure_history_hours=12: enough data to compute slopes reliably
      - pressure_slope_window_hours=3: classic "pressure tendency" window
    """
    # Import here so importing this module doesn't require HA unless you call this function.
    from homeassistant.util import dt as dt_util
    from homeassistant.components.recorder.history import state_changes_during_period

    now = dt_util.utcnow()

    # ----------------------------
    # 1) Read current values from HA state machine
    # ----------------------------
    wind_from_state = hass.states.get(wind_from_entity_id)
    wind_speed_state = hass.states.get(wind_speed_entity_id)

    wind_from_deg = _safe_float(wind_from_state.state if wind_from_state else None)
    wind_speed_kn = _safe_float(wind_speed_state.state if wind_speed_state else None)

    # ----------------------------
    # 2) Wind speed history (for wind trend)
    # ----------------------------
    wind_speed_start = now - timedelta(minutes=wind_speed_history_minutes)

    wind_speed_hist = await hass.async_add_executor_job(
        state_changes_during_period,
        hass,
        wind_speed_start,
        now,
        wind_speed_entity_id,
        True,  # no_attributes
    )

    wind_speed_vals: List[float] = []
    for st in wind_speed_hist.get(wind_speed_entity_id, []):
        fv = _safe_float(st.state)
        if fv is not None:
            wind_speed_vals.append(fv)

    # ----------------------------
    # 3) Wind direction history (for backing/veering detection)
    # ----------------------------
    wind_dir_delta = None
    if wind_dir_history_minutes and wind_dir_history_minutes > 0:
        wind_dir_start = now - timedelta(minutes=wind_dir_history_minutes)

        wind_dir_hist = await hass.async_add_executor_job(
            state_changes_during_period,
            hass,
            wind_dir_start,
            now,
            wind_from_entity_id,
            True,
        )

        wind_dir_vals: List[float] = []
        for st in wind_dir_hist.get(wind_from_entity_id, []):
            fv = _safe_float(st.state)
            if fv is not None:
                wind_dir_vals.append(fv)

        if len(wind_dir_vals) >= 2:
            wind_dir_delta = _circular_delta_deg(wind_dir_vals[0], wind_dir_vals[-1])

    # ----------------------------
    # 4) Pressure history + slope (hPa/hr) over last N hours
    # ----------------------------
    press_start = now - timedelta(hours=pressure_history_hours)

    press_hist = await hass.async_add_executor_job(
        state_changes_during_period,
        hass,
        press_start,
        now,
        pressure_entity_id,
        True,
    )

    press_vals: List[Tuple[Any, float]] = []
    for st in press_hist.get(pressure_entity_id, []):
        fv = _safe_float(st.state)
        if fv is not None:
            press_vals.append((st.last_updated, fv))

    pslope = None
    if press_vals:
        slope_start = now - timedelta(hours=pressure_slope_window_hours)
        window = [(t, v) for (t, v) in press_vals if t >= slope_start]
        if len(window) >= 2:
            t0, p0 = window[0]
            t1, p1 = window[-1]
            hours = (t1.timestamp() - t0.timestamp()) / 3600.0
            if hours > 0:
                pslope = (p1 - p0) / hours

    # ----------------------------
    # 5) Run the pure estimator and return the result
    # ----------------------------
    # Determine hemisphere (Buys-Ballot differs across the equator).
    # Prefer explicit latitude argument; otherwise fall back to HA config latitude if available.
    lat = latitude
    if lat is None:
        try:
            lat = float(getattr(hass.config, "latitude", None))
        except (TypeError, ValueError):
            lat = None
    hem = "south" if (lat is not None and lat < 0) else "north"

    return estimate_low_properties(
        wind_from_deg=wind_from_deg,
        pressure_slope_hpa_per_hr=pslope,
        wind_speed_kn=wind_speed_kn,
        wind_speed_history_kn=wind_speed_vals,
        wind_dir_delta_deg=wind_dir_delta,
        hemisphere=hem,
    )
