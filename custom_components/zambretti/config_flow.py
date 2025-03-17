import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector
from .options_flow import ZambrettiOptionsFlowHandler

from .const import DOMAIN, DEFAULT_PRESSURE_HISTORY_HOURS, DEFAULT_UPDATE_INTERVAL_MINUTE

class ZambrettiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Zambretti integration."""

    async def async_step_user(self, user_input=None):
        """Handle the initial step where the user selects sensors."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title="Zambretti Forecast", data=user_input)

        # ✅ Define schema with clear field names and suggested values
        schema = vol.Schema({
            vol.Required("wind_direction_sensor", description={"suggested_value": "sensor.wind_direction (360°)"}): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required("wind_speed_sensor_knots", description={"suggested_value": "sensor.wind_speed (knots)"}): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required("atmospheric_pressure_sensor", description={"suggested_value": "sensor.outside_pressure (hPa)"}): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required("temperature_sensor", description={"suggested_value": "sensor.outside_temperature (°C)"}): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required("humidity_sensor", description={"suggested_value": "sensor.outside_humidity (%)"}): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required("gps_location_latitude", description={"suggested_value": "sensor.gps_latitude"}): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required("gps_location_longitude", description={"suggested_value": "sensor.gps_longitude"}): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required("update_interval_minutes", default="10"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["1", "5", "10", "15", "20", "30", "60"],
                    mode=selector.SelectSelectorMode.DROPDOWN
                )
            ),            
            vol.Required("pressure_history_hours", default="3"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["3", "6", "9", "12"],
                    mode=selector.SelectSelectorMode.DROPDOWN
                )
            ),            
            vol.Required("fog_area_type", default="normal"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        "frequent_dense_fog",  # Highest fog likelihood
                        "fog_prone",           # Often foggy, but not extreme
                        "normal",              # Default setting
                        "rare_fog",            # Occasionally foggy
                        "hardly_ever_fog"        # Very rare fog
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN
                )
            )
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "info": "Please select the sensors for wind, pressure, temperature, humidity, and GPS."
            },
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return ZambrettiOptionsFlowHandler(config_entry)