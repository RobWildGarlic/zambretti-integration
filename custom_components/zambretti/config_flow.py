import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
)
from .options_flow import ZambrettiOptionsFlowHandler


class ZambrettiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Zambretti integration."""

    async def async_step_user(self, user_input=None) -> dict:
        """Handle the initial step where the user selects sensors."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title="Zambretti Forecast", data=user_input)

        # ✅ Define schema with clear field names and suggested values
        schema = vol.Schema(
            {
                vol.Required(
                    "wind_direction_sensor",
                    description={"suggested_value": "Sensor for wind direction (360°)"},
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    "wind_speed_sensor_knots",
                    description={"suggested_value": "Sensor for wind speed (knots)"},
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    "atmospheric_pressure_sensor",
                    description={
                        "suggested_value": "=Sensor for outside pressure (hPa)"
                    },
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    "temperature_sensor",
                    description={
                        "suggested_value": "Sensor for outside temperature (°C)"
                    },
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    "humidity_sensor",
                    description={"suggested_value": "Sensor for outside humidity (%)"},
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    "device_tracker_home",
                    description={
                        "suggested_value": "Device tracker for your location (usually home location)"
                    },
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="device_tracker")
                ),
                vol.Required(
                    "update_interval_minutes", default="10"
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["1", "5", "10", "15", "20", "30", "60"],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    "pressure_history_hours", default="3"
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["3", "6", "9", "12"],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    "fog_area_type", default="normal"
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            "frequent_dense_fog",  # Highest fog likelihood
                            "fog_prone",  # Often foggy, but not extreme
                            "normal",  # Default setting
                            "rare_fog",  # Occasionally foggy
                            "hardly_ever_fog",  # Very rare fog
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

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
        return ZambrettiOptionsFlowHandler()
