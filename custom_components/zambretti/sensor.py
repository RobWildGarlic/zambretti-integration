# HA imports
import asyncio
import logging
import time
from datetime import timedelta

import homeassistant.helpers.config_validation as cv

# Python imports
import voluptuous as vol
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import NoEntitySpecifiedError
from homeassistant.helpers.event import (
    async_track_time_interval,
)
from homeassistant.util import dt as dt_util  # ✅ Import HA's datetime utilities

from .ai_prompt import build_ai_prompt

# Zambretti imports
from .const import DOMAIN, Z_DEBUG
from .fog_analysis import determine_fog_chance
from .helpers import alert_desc, safe_float

# from .low_estimator import estimate_low_properties
from .low_estimator import async_estimate_low_properties
from .pressure_analysis import determine_pressure_trend, get_normal_pressure
from .region import determine_region
from .temperature_analysis import determine_temperature_effect
from .weather_processing import zambretti_forecast
from .weather_processing_advanced import generate_pressure_forecast_advanced
from .wind_analysis import (
    calculate_most_frequent_wind_direction,
    determine_wind_direction,
    determine_wind_speed,
)
from .wind_systems import wind_systems

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up the Zambretti sensor from a config entry."""
    _LOGGER.debug(
        "✅ async_setup_entry() called for Zambretti, entry_id: %s", entry.entry_id
    )

    sensor = Zambretti(hass, entry)
    async_add_entities([sensor], update_before_add=True)

    # Store reference so the service can update all instances
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault("entities", [])
    hass.data[DOMAIN]["entities"].append(sensor)

    # Register the force_update service (once)
    if not hass.data[DOMAIN].get("service_registered"):
        hass.data[DOMAIN]["service_registered"] = True

        SERVICE_FORCE_UPDATE = "force_update"

        SERVICE_FORCE_UPDATE_SCHEMA = vol.Schema(
            {
                vol.Optional("entity_id"): vol.Any("all", cv.entity_ids),
            }
        )

        async def async_handle_force_update_service(call):
            """Force update one or more Zambretti sensors."""
            entity_id = call.data.get("entity_id")

            entities = hass.data.get(DOMAIN, {}).get("entities", [])

            # Determine targets
            if entity_id is None or entity_id == "all":
                targets = list(entities)
            else:
                wanted = set(entity_id)
                targets = [
                    e for e in entities if getattr(e, "entity_id", None) in wanted
                ]

            if not targets:
                _LOGGER.warning(
                    "⚠️ zambretti.force_update: no matching entities found for entity_id=%s",
                    entity_id,
                )
                return

            _LOGGER.info(
                "🔧 zambretti.force_update called for %s entities (entity_id=%s)",
                len(targets),
                entity_id,
            )

            # Run updates sequentially to avoid DB/history storms
            for ent in targets:
                try:
                    await ent.async_update()
                except Exception as err:
                    _LOGGER.exception(
                        "❌ zambretti.force_update failed for %s: %s",
                        getattr(ent, "entity_id", "unknown"),
                        err,
                    )

        hass.services.async_register(
            DOMAIN,
            SERVICE_FORCE_UPDATE,
            async_handle_force_update_service,
            schema=SERVICE_FORCE_UPDATE_SCHEMA,
        )
        _LOGGER.debug("✅ Registered service: %s.%s", DOMAIN, SERVICE_FORCE_UPDATE)

    # Remove SCAN_INTERVAL if you are using dynamic scheduling
    # SCAN_INTERVAL = timedelta(minutes=10)  # <-- remove this

    # Create a time-based update callback
    async def async_time_based_update(now):
        """Trigger an update on the sensor."""
        _LOGGER.debug("⏳ Time-based update triggered for Zambretti.")
        await sensor.async_update_ha_state(force_refresh=True)

    # Read user-selected interval from the config (defaults to 1 minute if not set)
    update_interval = int(safe_float(entry.options.get("update_interval_minutes", 1)))

    # Schedule time-based updates at the selected interval
    async_track_time_interval(
        hass, async_time_based_update, timedelta(minutes=update_interval)
    )

    _LOGGER.debug(
        "✅ Registered time-based updates every %s minute(s).", update_interval
    )


class Zambretti(SensorEntity):
    """Zambretti Weather Forecast Sensor."""

    should_poll = False  # Since we are manually scheduling updates

    def __init__(self, hass, entry):
        self.hass = hass
        self._state = "Initializing"
        self.config_entry = entry  # ✅ Store config_entry for access later
        self.config = {**entry.data, **entry.options}  # ✅ Merge data and options

        # Load configuration parameters
        self._load_config()

        # ✅ Get the unique entry_id
        self.entry_id = entry.entry_id
        _LOGGER.debug(
            f"__init__✅ Zambretti sensor received unique_id: {self.entry_id}"
        )

        # ✅ Unique ID from HA, stable even if sensors are updated
        self._attr_unique_id = f"{DOMAIN}_{self.entry_id}"

        # ✅ Ensure a name is set, or HA may discard it
        self._attr_name = "Zambretti Forecast"
        _LOGGER.debug(
            f"__init__✅ Initialized Zambretti sensor with unique_id: {self._attr_unique_id}"
        )

        # Zet counter for "waiting for sensors" state
        self.counter = 0

        # attributes for Zambretti sensor
        self._attributes = {
            "icon": "mdi:zend",
            # Forecast Advanced, based on pressure development 3hr, 6hr and 12hr
            "forecast_advanced": None,
            # 🚨 Alert System
            "alert_level": 0,
            "alert": None,
            # 🌍 Location & Regional Information
            "region": None,
            "region_url": None,
            # 🏴‍☠️ Wind & Weather Systems
            "wind_system": None,
            "wind_system_urls": None,
            # 🌫️ Fog & Humidity
            "fog_chance": None,
            "fog_chance_pct": None,
            "dewpoint": None,
            "humidity": None,
            "temp_diff_fog": None,
            # 🌡️ Temperature Effects
            "temp_effect": None,
            "temperature_diff_hour": None,
            # 🌬️ Wind Information
            "wind_speed": None,
            "wind_direction": None,
            "estimated_wind_speed": None,
            "estimated_max_wind_speed": None,
            "wind_forecast": None,
            "wind_direction_change": None,
            # ⬇️ Atmospheric Pressure
            "normal_pressure": None,
            "pressure": None,
            "pressure_trend": None,
            "pressure_move_per_hour": None,
            "pressure analysis": None,
            "method_used": None,
            "method_deviation": None,
            # Number of history entities read
            "hist_wind_speed": None,
            "hist_wind_direction": None,
            "hist_pressure": None,
            "hist_temperature": None,
            # 📡 Sensor Data (Raw Readings)
            "sensor_latitude": None,
            "sensor_longitude": None,
            "sensor_wind_direction": None,
            "sensor_wind_speed": None,
            "sensor_humidity": None,
            "sensor_temperature": None,
            "sensor_pressure": None,
            # Low pressure data
            "low_direction": None,
            "low_direction_deg": None,
            "low_distance_class": None,
            "low_distance_km_range": None,
            "low_wind_trend_class": None,
            "low_wind_trend_delta_kn": None,
            "low_estimate_confidence": None,
            "low_weather_trend": None,
            "low_time_to_impact": None,
            "low_time_to_impact_range": None,
            "low_relative_position": None,
            "low_movement": None,
            "impact_window_status": None,
            "low_wind_rotation_likely": None,
            "low_wind_dir_delta_deg": None,
            "low_frontal_zone": None,
            "low_anchoring_risk": None,
            "low_summary": None,
            # AI prompt output
            "ai_prompt": None,
            "ai_history_pressure_hpa": None,
            "ai_history_temperature_c": None,
            "ai_history_wind_speed_kn": None,
            "ai_history_wind_direction": None,
            "ai_history_meta": None,
            # other Configuration
            "cfg_update_interval_minutes": None,
            "cfg_pressure_history_hours": None,
            "cfg_fog_area_type": None,
            # 🕒 Metadata
            "last_updated": None,
            "prev_update": "N/A",
            "fully_started": False,
            # debug data
            "dbg_len_state": None,
        }
        _LOGGER.debug("__init__✅ Zambretti sensor _init_ ran")

    @property
    def name(self):
        """Return the name of the entity."""
        return self._attr_name  # ✅ Ensure name is defined

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes

    async def async_update(self):
        """Fetch sensor data from HA and update the entity state."""

        t0_total = time.perf_counter()

        _LOGGER.debug("✅ entering async_update.")

        # Reload configuration every update (to apply changes)
        self.config = {**self.config_entry.data, **self.config_entry.options}
        self._load_config()  # Reload configuration values

        # -------------------------------
        # If HA is starting up then not all required sensors
        # provide data yet. So wait for alle sensors to be on-line
        # -------------------------------
        required_sensors = [
            self.atmospheric_pressure_sensor,
            self.wind_direction_sensor,
            self.device_tracker_home,
            self.temperature_sensor,
            self.humidity_sensor,
            self.wind_speed_sensor_knots,
        ]
        # if not all required sensors are available yet then try again later
        if not self.sensors_valid(required_sensors):
            _LOGGER.debug(
                "⚠️ Required sensors not yet available. Scheduling re-check in 10 seconds."
            )
            self.counter += 1
            self._state = f"Zambretti waiting for sensors ... attempt {self.counter}"
            # Push the updated state to HA immediately
            t_pub0 = time.perf_counter()
            try:
                self.async_write_ha_state()
            except NoEntitySpecifiedError:
                _LOGGER.debug(
                    "Entity not yet registered; skipping async_write_ha_state()."
                )
            t_publish_ms = (time.perf_counter() - t_pub0) * 1000.0

            t_total_ms = (time.perf_counter() - t0_total) * 1000.0
            t_compute_ms = max(t_total_ms - t_publish_ms, 0.0)

            if Z_DEBUG:
                _LOGGER.info(
                    "⏱️ Zambretti perf (%s): total=%.1fms compute=%.1fms publish=%.1fms",
                    getattr(self, "entity_id", "unknown"),
                    t_total_ms,
                    t_compute_ms,
                    t_publish_ms,
                )

            # Schedule a re-check in 10 seconds without blocking startup
            loop = asyncio.get_running_loop()
            loop.call_later(10, lambda: loop.create_task(self.async_update()))
            return

        # set starting point for alert level
        alert_level, t_alert_level = 0, 0

        # -------------------------------
        # Read sensors
        # -------------------------------
        pressure_state = self.hass.states.get(self.atmospheric_pressure_sensor)
        wind_direction_state = self.hass.states.get(self.wind_direction_sensor)
        device_tracker_home_state = self.hass.states.get(self.device_tracker_home)
        temperature_state = self.hass.states.get(self.temperature_sensor)
        humidity_state = self.hass.states.get(self.humidity_sensor)
        wind_speed_state = self.hass.states.get(self.wind_speed_sensor_knots)

        # -------------------------------
        # Update sensor attributes
        # -------------------------------
        self._attributes["sensor_wind_speed"] = wind_speed_state.state
        self._attributes["sensor_wind_direction"] = wind_direction_state.state
        self._attributes["sensor_humidity"] = humidity_state.state
        self._attributes["sensor_temperature"] = temperature_state.state
        self._attributes["sensor_pressure"] = pressure_state.state

        # -------------------------------
        # Update other config entries
        # -------------------------------
        self._attributes["cfg_update_interval_minutes"] = self.update_interval_minutes
        self._attributes["cfg_pressure_history_hours"] = self.pressure_history_hours
        self._attributes["cfg_fog_area_type"] = self.fog_area_type

        # -------------------------------
        # Populate Sensor Data & Convert Values
        # -------------------------------
        pressure = safe_float(pressure_state.state)
        wind_speed = safe_float(wind_speed_state.state)
        wind_direction = safe_float(wind_direction_state.state)
        humidity = safe_float(humidity_state.state)
        temperature = safe_float(temperature_state.state)

        # -------------------------------
        # Retrieve, populate and store lat/lon
        # -------------------------------
        if (
            device_tracker_home_state
            and "latitude" in device_tracker_home_state.attributes
        ):
            latitude = safe_float(device_tracker_home_state.attributes["latitude"])
            longitude = safe_float(device_tracker_home_state.attributes["longitude"])
            _LOGGER.debug(f"Device Tracker Location: lat={latitude}, lon={longitude}")
        else:
            _LOGGER.warning(
                "Could not retrieve latitude and longitude from device tracker!"
            )
        self._attributes["sensor_latitude"] = latitude
        self._attributes["sensor_longitude"] = longitude

        # -------------------------------
        # -------------------------------
        # PREP DONE, LET'S GET GOING CREATING THE FORECAST
        # -------------------------------
        # -------------------------------

        # -------------------------------
        # Determine Region
        # -------------------------------
        region, region_name, region_url = determine_region(latitude, longitude)
        self._attributes.update(
            {
                "region": region_name,
                "region_url": region_url,
            }
        )

        # -------------------------------
        # Determine normal pressure for Region in current month
        # -------------------------------
        normal_pressure = get_normal_pressure(region)
        self._attributes.update(
            {
                "normal_pressure": normal_pressure,
                "pressure": pressure,
            }
        )

        # -------------------------------
        # Analyze Atmospheric Pressure
        # -------------------------------
        (
            trend,
            slope,
            p_analysis,
            hist_pressure,
            method_used,
            method_deviation,
        ) = await determine_pressure_trend(
            self.hass, self.atmospheric_pressure_sensor, self.pressure_history_hours
        )
        _LOGGER.debug(
            f"SENSOR: Straight-line slope: {slope}, Avg deviation: {method_deviation}"
        )
        self._attributes.update(
            {
                "pressure_trend": trend,
                "pressure_move_per_hour": slope,
                "pressure analysis": p_analysis,
                "hist_pressure": hist_pressure,
                "method_deviation": method_deviation,
                "method_used": method_used,
            }
        )
        _LOGGER.debug(f"Pressure analyzed: {trend} ({slope} hPa)")

        # -------------------------------
        # Determine average Wind Speed
        # -------------------------------
        current_wind_speed, hist_wind_speed = await determine_wind_speed(
            self.hass, self.wind_speed_sensor_knots
        )
        self._attributes.update(
            {
                "wind_speed": wind_speed,
                "hist_wind_speed": hist_wind_speed,
            }
        )
        _LOGGER.debug(f"Wind speed analyzed: {current_wind_speed}")

        # -------------------------------
        # Determine Wind Direction
        # -------------------------------
        (
            wind_direction,
            hist_wind_direction,
        ) = await calculate_most_frequent_wind_direction(
            self.hass, self.wind_direction_sensor
        )
        self._attributes.update(
            {
                "wind_direction": wind_direction,
                "hist_wind_direction": hist_wind_direction,
            }
        )
        _LOGGER.debug(f"Wind direction analyzed: {wind_direction}")

        # -------------------------------
        # Analyze Wind Direction Change
        # -------------------------------
        wind_direction_change = determine_wind_direction(wind_direction, trend)
        self._attributes.update(
            {
                "wind_direction_change": wind_direction_change,
            }
        )
        _LOGGER.debug(f"Wind direction change analyzed: {wind_direction_change}")

        # -------------------------------
        # Analyze Temperature Trends
        # -------------------------------
        (
            temp_effect,
            temp_diff_hour,
            hist_temperature,
            t_alert_level,
        ) = await determine_temperature_effect(self.hass, self.temperature_sensor)
        self._attributes.update(
            {
                "temperature_diff_hour": temp_diff_hour,
                "temp_effect": temp_effect,
                "hist_temperature": hist_temperature,
            }
        )
        _LOGGER.debug(f"Temperature effect analyzed: {temp_effect}")
        alert_level = max(alert_level, t_alert_level)

        # -------------------------------
        # Analyze low pressure location and consequences for wind
        # -------------------------------
        low = await async_estimate_low_properties(
            hass=self.hass,
            wind_from_entity_id=self.wind_direction_sensor,
            wind_speed_entity_id=self.wind_speed_sensor_knots,
            pressure_entity_id=self.atmospheric_pressure_sensor,
            wind_speed_history_minutes=90,
            wind_dir_history_minutes=120,
            pressure_history_hours=12,
            pressure_slope_window_hours=3,
            latitude=latitude,  # ✅ your live GPS latitude
        )

        _LOGGER.warning(
            "LOW DEBUG: wind_dir=%s wind_speed=%s pressure=%s",
            self.hass.states.get(self.wind_direction_sensor),
            self.hass.states.get(self.wind_speed_sensor_knots),
            self.hass.states.get(self.atmospheric_pressure_sensor),
        )

        self._attributes.update(
            {
                # existing
                "low_direction": low.low_bearing_compass,
                "low_direction_deg": low.low_bearing_deg,
                "low_distance_class": low.distance_class,
                "low_distance_km_range": low.distance_km_range,
                "low_wind_trend_class": low.wind_trend,
                "low_wind_trend_delta_kn": low.wind_delta_kn
                if low.wind_delta_kn is not None
                else "Unknown",
                "low_estimate_confidence": low.confidence,
                "low_weather_trend": low.weather_trend,
                "low_relative_position": low.low_relative_position,
                "low_movement": low.low_movement,
                "impact_window_status": low.impact_window_status,
                "low_time_to_impact": low.time_to_impact,
                "low_time_to_impact_range": low.time_to_impact_range,
                "low_wind_rotation_likely": low.wind_rotation_likely,
                "low_wind_dir_delta_deg": low.wind_dir_delta_deg
                if low.wind_dir_delta_deg is not None
                else "Unknown",
                "low_frontal_zone": low.frontal_zone
                if low.frontal_zone is not None
                else "Unknown",
                "low_anchoring_risk": low.anchoring_risk,
                "low_summary": low.summary,
            }
        )

        # -------------------------------
        # Calculate Fog Probability
        # -------------------------------
        fog_chance, fog_chance_pct, dewpoint, temp_diff, t_alert_level = (
            determine_fog_chance(
                humidity,
                temperature,
                wind_speed,
                self.fog_area_type,  # User-defined fog area type
            )
        )
        self._attributes.update(
            {
                "fog_chance": fog_chance,
                "fog_chance_pct": round(fog_chance_pct, 0),
                "dewpoint": round(dewpoint, 2),
                "temp_diff_fog": int(temp_diff),
                "humidity": humidity,
            }
        )
        _LOGGER.debug(f"Fog chance analyzed: {fog_chance}")
        alert_level = max(alert_level, t_alert_level)

        # -------------------------------
        # Generate Forecast
        # -------------------------------
        (
            forecast,
            self._attributes["icon"],
            t_alert_level,
            estimated_wind_speed,
            estimated_max_wind_speed,
        ) = await zambretti_forecast(
            pressure, slope, trend, current_wind_speed, temperature, normal_pressure
        )
        alert_level = max(alert_level, t_alert_level)

        # -------------------------------
        # Generate advanced forecast, based on development over 3hr, 6hr and 12hr
        # -------------------------------
        forecast_advanced = await generate_pressure_forecast_advanced(
            self.hass, self.atmospheric_pressure_sensor, pressure, region, short=False
        )
        self._attributes.update(
            {
                "forecast_advanced": forecast_advanced,
            }
        )

        # -------------------------------
        # Generate AI prompt + 24h history
        # -------------------------------
        try:
            ai = await build_ai_prompt(
                self.hass,
                pressure_entity_id=self.atmospheric_pressure_sensor,
                temperature_entity_id=self.temperature_sensor,
                wind_speed_entity_id=self.wind_speed_sensor_knots,
                wind_direction_entity_id=self.wind_direction_sensor,
                z_attrs=self._attributes,  # use everything you already computed
                history_hours=24,
                sample_minutes=60,  # hourly samples (keeps attribute size sane)
            )

            self._attributes["ai_prompt"] = ai["prompt"]

            hist = ai["history"]
            self._attributes["ai_history_pressure_hpa"] = hist.get("pressure_hpa", [])
            self._attributes["ai_history_temperature_c"] = hist.get("temperature_c", [])
            self._attributes["ai_history_wind_speed_kn"] = hist.get("wind_speed_kn", [])
            self._attributes["ai_history_wind_direction"] = hist.get(
                "wind_direction", []
            )
            self._attributes["ai_history_meta"] = hist.get("meta", {})

        except Exception as e:
            _LOGGER.debug("AI prompt build failed: %s", e)

        # -------------------------------
        # We now have everythong to make up a full forecast
        # -------------------------------
        estimated_wind_speeds = f"{int(safe_float(estimated_wind_speed) * 0.8)}-{int(safe_float(estimated_wind_speed) * 1.2)}"
        wind_forecast = (
            f"Wind estimate {estimated_wind_speeds}kn, {wind_direction_change}"
        )
        full_forecast = f"{p_analysis}. {forecast}. {wind_forecast}. {fog_chance} right now. {temp_effect}."

        self._state = full_forecast
        self._attributes.update(
            {
                "estimated_wind_speed": estimated_wind_speed,
                "estimated_max_wind_speed": estimated_max_wind_speed,
                "wind_forecast": wind_forecast,
            }
        )

        # -------------------------------
        # Generate Wind System Data
        # -------------------------------
        wind_system, system_urls = wind_systems(
            region,
            region_name,
            region_url,
            latitude,
            longitude,
            wind_direction,
            current_wind_speed,
        )
        _LOGGER.debug(f"SENSOR: {wind_system} {system_urls}")
        self._attributes.update(
            {
                "wind_system": wind_system,
                "wind_system_urls": system_urls,
            }
        )

        # -------------------------------
        # Update Alert Level Based on Wind Speed
        # -------------------------------
        if safe_float(estimated_max_wind_speed) > 50:
            alert_level = 5.1 if alert_level <= 5 else alert_level
        elif safe_float(estimated_max_wind_speed) > 40:
            alert_level = 4.1 if alert_level <= 4 else alert_level
        elif safe_float(estimated_max_wind_speed) > 30:
            alert_level = 3.1 if alert_level <= 3 else alert_level
        elif safe_float(estimated_max_wind_speed) > 25:
            alert_level = 2.2 if alert_level <= 2 else alert_level
        elif safe_float(estimated_max_wind_speed) > 20:
            alert_level = 2.1 if alert_level <= 2 else alert_level

        # -------------------------------
        # Update Metadata & Finalize
        # -------------------------------
        last_updated_str = dt_util.as_local(dt_util.utcnow()).strftime("%H:%M")

        self._attributes["prev_update"] = self._attributes.get("last_updated", "None")

        self._attributes.update(
            {
                "alert_level": alert_level,
                "alert": alert_desc(alert_level),
                "last_updated": last_updated_str,
                "fully_started": True,
                "dbg_len_state": len(self._state),
            }
        )

        # Compute timing for everything above
        t_compute_ms = (time.perf_counter() - t0_total) * 1000.0

        # Push for an update of Zambretti sensor
        t_pub0 = time.perf_counter()
        try:
            self.async_write_ha_state()
        except NoEntitySpecifiedError:
            _LOGGER.debug("Entity not yet registered; skipping async_write_ha_state().")
        t_publish_ms = (time.perf_counter() - t_pub0) * 1000.0

        t_total_ms = (time.perf_counter() - t0_total) * 1000.0

        _LOGGER.info(
            "⏱️ Zambretti perf (%s): total=%.1fms compute=%.1fms publish=%.1fms",
            getattr(self, "entity_id", "unknown"),
            t_total_ms,
            t_compute_ms,
            t_publish_ms,
        )

        _LOGGER.debug("✅ Entity updated successfully.")

    async def async_update_options(self, entry):
        """Handle options update."""
        _LOGGER.debug("🔄 Configuration updated, reloading sensor settings.")
        self.config = {**entry.data, **entry.options}
        self._load_config()
        await self.async_update()

    def _load_config(self):
        """Load configuration values from entry data/options."""
        _LOGGER.debug("🔄 Loading configuration from config entry.")

        # ✅ Fetch values from the stored config
        self.wind_direction_sensor = self.config.get("wind_direction_sensor", None)
        self.wind_speed_sensor_knots = self.config.get("wind_speed_sensor_knots", None)

        self.atmospheric_pressure_sensor = self.config.get(
            "atmospheric_pressure_sensor", None
        )
        self.temperature_sensor = self.config.get("temperature_sensor", None)
        self.humidity_sensor = self.config.get("humidity_sensor", None)

        self.device_tracker_home = self.config.get("device_tracker_home", None)

        self.pressure_history_hours = self.config.get(
            "pressure_history_hours", 3
        )  # Default 3 hours
        self.fog_area_type = self.config.get(
            "fog_area_type", "normal"
        )  # Default to 'normal'
        self.update_interval_minutes = self.config.get(
            "update_interval_minutes", 10
        )  # Default to 'normal'

        _LOGGER.debug(
            f"✅ Config loaded: Pressure={self.atmospheric_pressure_sensor}, Wind={self.wind_speed_sensor_knots}, "
            f"Temp={self.temperature_sensor}, Humidity={self.humidity_sensor}, "
            f"History Hours={self.pressure_history_hours}, Fog Area={self.fog_area_type}"
        )

    def sensors_valid(self, sensor_ids):
        """Return True if all sensors exist and their state is valid."""
        for sensor in sensor_ids:
            state_obj = self.hass.states.get(sensor)
            if not state_obj or state_obj.state in (None, "unknown", "unavailable"):
                return False
        return True


# ===============================================================================================
