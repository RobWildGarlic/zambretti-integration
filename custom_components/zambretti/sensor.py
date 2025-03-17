#HA imports
from homeassistant.util import dt as dt_util  # ✅ Import HA's datetime utilities
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.components.recorder import history
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_state_change, async_track_time_interval, async_call_later
from homeassistant.exceptions import NoEntitySpecifiedError
#Zambretti imports
from .const import DOMAIN, Z_DEBUG
from .wind_systems import wind_systems, determine_region
from .helpers import safe_float, alert_desc
from .weather_processing import zambretti_forecast
from .wind_analysis import determine_wind_speed, calculate_most_frequent_wind_direction, determine_wind_direction
from .pressure_analysis import determine_pressure_trend
from .temperature_analysis import determine_temperature_effect
from .fog_analysis import determine_fog_chance

#Python imports
import voluptuous as vol
import math, asyncio
from datetime import timedelta

import logging
_LOGGER = logging.getLogger(__name__)

CONF_PRESSURE = "sensor.outside_pressure"
CONF_WIND_DIRECTION_DEGREES = "sensor.wind_direction_for_windrose"
CONF_LATITUDE = "sensor.boat_gps_location_latitude"
CONF_LONGITUDE = "sensor.boat_gps_location_longitude"
CONF_TEMPERATURE = "sensor.outside_temperature"
CONF_HUMIDITY = "sensor.outside_humidity"
CONF_WIND_SPEED = "sensor.nmea2000_130306_wind_speed_knots"
CONF_PRESSURE_HISTORY_HOURS = 3
CONF_FOG_AREA_TYPE = "normal"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Zambretti sensor from a config entry."""
    _LOGGER.debug("✅ async_setup_entry() called for Zambretti, entry_id: %s", entry.entry_id)

    sensor = Zambretti(hass, entry)
    async_add_entities([sensor], update_before_add=True)

    # Remove SCAN_INTERVAL if you’re using dynamic scheduling
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

    _LOGGER.debug("✅ Registered time-based updates every %s minute(s).", update_interval)

class Zambretti(SensorEntity):
    """Zambretti Weather Forecast Sensor."""

    should_poll = False  # Since we’re manually scheduling updates

    def __init__(self, hass, entry):
        self.hass = hass
        self._state = "Initializing"
        self.config_entry = entry  # ✅ Store config_entry for access later
        self.config = {**entry.data, **entry.options}  # ✅ Merge data and options

        # Load configuration parameters
        self._load_config()
        
        # ✅ Get the unique entry_id
        self.entry_id = entry.entry_id  
        _LOGGER.debug(f"__init__✅ Zambretti sensor received unique_id: {self.entry_id}")
#        self.config = entry.data  # ✅ Store user-configured sensors

        # ✅ Unique ID from HA, stable even if sensors are updated
        self._attr_unique_id = f"{DOMAIN}_{self.entry_id}"
#        self._attr_unique_id = f"Forecast"

        # ✅ Ensure a name is set, or HA may discard it
        self._attr_name = f"Zambretti Forecast"
        _LOGGER.debug(f"__init__✅ Initialized Zambretti sensor with unique_id: {self._attr_unique_id}")
        
        # Zet counter for "waiting for sensors" state
        self.counter = 0

        # required sensors, from the gui config
#        self.wind_direction_sensor = self.config["wind_direction_sensor"]
#        self.wind_speed_sensor_knots = self.config["wind_speed_sensor_knots"]
#        self.atmospheric_pressure_sensor = self.config["atmospheric_pressure_sensor"]
#        self.temperature_sensor = self.config["temperature_sensor"]
#        self.humidity_sensor = self.config["humidity_sensor"]
#        self.gps_location_latitude = self.config["gps_location_latitude"]
#        self.gps_location_longitude = self.config["gps_location_longitude"]
        # Other config settings
#        self.pressure_history_hours = self.config.get("pressure_history_hours", 3)
#        self.fog_area_type = entry.options.get("fog_area_type", entry.data.get("fog_area_type", "normal"))        

        # attributes for Zambretti sensor
        self._attributes = {
            "icon": "mdi:zend",
        
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
            "pressure_trend": None,
            "pressure_move_per_hour": None,
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
        _LOGGER.debug(f"__init__✅ Zambretti sensor _init_ ran")
        
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

        _LOGGER.debug(f"✅ entering async_update.")

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
            self.gps_location_latitude,
            self.gps_location_longitude,
            self.temperature_sensor,
            self.humidity_sensor,
            self.wind_speed_sensor_knots,
        ]
        # if not all required sensors are available yet then try again later
        if not self.sensors_valid(required_sensors):
            _LOGGER.debug("⚠️ Required sensors not yet available. Scheduling re-check in 10 seconds.")
            self.counter += 1
            self._state = f"Zambretti waiting for sensors ... attempt {self.counter}"
            # Push the updated state to HA immediately
            try:
                self.async_write_ha_state()
            except NoEntitySpecifiedError:
                _LOGGER.debug("Entity not yet registered; skipping async_write_ha_state().")
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
        latitude_state = self.hass.states.get(self.gps_location_latitude)
        longitude_state = self.hass.states.get(self.gps_location_longitude)
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
        self._attributes["sensor_latitude"] = latitude_state.state
        self._attributes["sensor_longitude"] = longitude_state.state
        
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
        pressure_history_hours = int(safe_float(self.pressure_history_hours))

        # -------------------------------
        # Analyze Atmospheric Pressure
        # -------------------------------
        trend, slope, hist_pressure, method_used, method_deviation = await \
            determine_pressure_trend(
                self.hass,
                self.atmospheric_pressure_sensor,
                self.pressure_history_hours
            )
        self._attributes.update({
            "pressure_trend": trend,
            "pressure_move_per_hour": slope,
            "hist_pressure": hist_pressure,
            "method_deviation": method_deviation,
            "method_used": method_used,

        })
        _LOGGER.debug(f"ℹ️ Pressure analyzed: {trend} ({slope} hPa)")

        # -------------------------------
        # Determine average Wind Speed
        # -------------------------------
        current_wind_speed, hist_wind_speed = await determine_wind_speed(
            self.hass,
            self.wind_speed_sensor_knots
        )
        self._attributes.update({
            "wind_speed": wind_speed,
            "hist_wind_speed": hist_wind_speed,
        })
        _LOGGER.debug(f"ℹ️ Wind speed analyzed: {current_wind_speed}")

        # -------------------------------
        # Determine Wind Direction
        # -------------------------------
        wind_direction, hist_wind_direction = await calculate_most_frequent_wind_direction(
            self.hass,
            self.wind_direction_sensor
        )
        self._attributes.update({
            "wind_direction": wind_direction,
            "hist_wind_direction": hist_wind_direction,
        })
        _LOGGER.debug(f"ℹ️ Wind direction analyzed: {wind_direction}")

        # -------------------------------
        # Analyze Wind Direction Change
        # -------------------------------
        wind_direction_change = determine_wind_direction(wind_direction, trend)
        self._attributes.update({
            "wind_direction_change": wind_direction_change,
        })
        _LOGGER.debug(f"ℹ️ Wind direction change analyzed: {wind_direction_change}")

        # -------------------------------
        # Retrieve GPS Location
        # -------------------------------
        latitude = safe_float(latitude_state.state)
        longitude = safe_float(longitude_state.state)
        _LOGGER.debug(f"ℹ️ GPS location established: {latitude}, {longitude}")

        # -------------------------------
        # Analyze Temperature Trends
        # -------------------------------
        temp_effect, temp_diff_hour, hist_temperature, t_alert_level = await \
            determine_temperature_effect(
                self.hass,
                self.temperature_sensor
            )
        self._attributes.update({
            "temperature_diff_hour": temp_diff_hour,
            "temp_effect": temp_effect,
            "hist_temperature": hist_temperature,
        })
        _LOGGER.debug(f"ℹ️ Temperature effect analyzed: {temp_effect}")
        alert_level = max(alert_level, t_alert_level)

        # -------------------------------
        # Calculate Fog Probability
        # -------------------------------
        fog_chance, fog_chance_pct, dewpoint, temp_diff, t_alert_level = \
            determine_fog_chance(
                humidity,
                temperature,
                wind_speed,
                self.fog_area_type  # User-defined fog area type
            )
        self._attributes.update({
            "fog_chance": fog_chance,
            "fog_chance_pct": round(fog_chance_pct, 0),
            "dewpoint": round(dewpoint, 2),
            "temp_diff_fog": int(temp_diff),
            "humidity": humidity,
        })
        _LOGGER.debug(f"ℹ️ Fog chance analyzed: {fog_chance}")
        alert_level = max(alert_level, t_alert_level)

        # -------------------------------
        # Generate Forecast
        # -------------------------------
        (forecast, self._attributes["icon"], t_alert_level, estimated_wind_speed, 
         estimated_max_wind_speed) = await zambretti_forecast(
            pressure,
            slope,
            trend,
            current_wind_speed,
            temperature
        )
        alert_level = max(alert_level, t_alert_level)
        
        # We now have everythong to make up a full forecast
        estimated_wind_speeds = f"{int(safe_float(estimated_wind_speed)*0.8)}-{int(safe_float(estimated_wind_speed)*1.2)}"
        wind_forecast = f"Wind estimate {estimated_wind_speeds}kn, {wind_direction_change}"
        full_forecast = f"{forecast} {wind_forecast}. {fog_chance}. {temp_effect}."
        
        self._state = full_forecast
        self._attributes.update({
            "estimated_wind_speed": estimated_wind_speed,
            "estimated_max_wind_speed": estimated_max_wind_speed,
            "wind_forecast": wind_forecast,
        })

        # -------------------------------
        # Determine Region
        # -------------------------------
        region, region_url = determine_region(latitude, longitude)
        region_name = region.replace("_", " ").title()
        self._attributes.update({
            "region": region_name,
            "region_url": region_url,
        })

        # -------------------------------
        # Generate Wind System Data
        # -------------------------------
        wind_system, system_urls = wind_systems(
            region,
            region_url,
            latitude,
            longitude,
            wind_direction,
            current_wind_speed
        )
        _LOGGER.debug(f"SENSOR: {wind_system} {system_urls}")
        self._attributes.update({
            "wind_system": wind_system,
            "wind_system_urls": system_urls,
        })

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
                   
        self._attributes.update({
            "alert_level": alert_level,
            "alert": alert_desc(alert_level),
            "last_updated": last_updated_str,
            "fully_started": True,
            "dbg_len_state": len(self._state),
        })
        
        # Push for an update of Zambretti sensor
        try:
            self.async_write_ha_state()
        except NoEntitySpecifiedError:
            _LOGGER.debug("Entity not yet registered; skipping async_write_ha_state().")


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
        
        self.atmospheric_pressure_sensor = self.config.get("atmospheric_pressure_sensor", None)
        self.temperature_sensor = self.config.get("temperature_sensor", None)
        self.humidity_sensor = self.config.get("humidity_sensor", None)
        
        self.gps_location_latitude = self.config.get("gps_location_latitude", None)
        self.gps_location_longitude = self.config.get("gps_location_longitude", None)
        
        self.pressure_history_hours = self.config.get("pressure_history_hours", 3)  # Default 3 hours
        self.fog_area_type = self.config.get("fog_area_type", "normal")  # Default to 'normal'
        self.update_interval_minutes = self.config.get("update_interval_minutes", 10)  # Default to 'normal'

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
#===============================================================================================
