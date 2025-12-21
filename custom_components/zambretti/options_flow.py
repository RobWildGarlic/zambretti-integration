import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

class ZambrettiOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Zambretti options flow for modifying settings after setup."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        entry = self.config_entry  # provided by HA (read-only)

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema({
            vol.Required(
                "wind_direction_sensor",
                default=entry.options.get("wind_direction_sensor", entry.data.get("wind_direction_sensor", ""))
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),

            vol.Required(
                "wind_speed_sensor_knots",
                default=entry.options.get("wind_speed_sensor_knots", entry.data.get("wind_speed_sensor_knots", ""))
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),

            vol.Required(
                "atmospheric_pressure_sensor",
                default=entry.options.get("atmospheric_pressure_sensor", entry.data.get("atmospheric_pressure_sensor", ""))
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),

            vol.Required(
                "temperature_sensor",
                default=entry.options.get("temperature_sensor", entry.data.get("temperature_sensor", ""))
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),

            vol.Required(
                "humidity_sensor",
                default=entry.options.get("humidity_sensor", entry.data.get("humidity_sensor", ""))
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),

            vol.Required(
                "device_tracker_home",
                default=entry.options.get("device_tracker_home", entry.data.get("device_tracker_home", ""))
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="device_tracker")),

            # These selectors return strings, so keep defaults as strings too
            vol.Required(
                "update_interval_minutes",
                default=str(entry.options.get("update_interval_minutes", entry.data.get("update_interval_minutes", "10")))
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["1", "5", "10", "15", "20", "30", "60"],
                    mode=selector.SelectSelectorMode.DROPDOWN
                )
            ),

            vol.Required(
                "pressure_history_hours",
                default=str(entry.options.get("pressure_history_hours", entry.data.get("pressure_history_hours", "3")))
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["3", "6", "9", "12"],
                    mode=selector.SelectSelectorMode.DROPDOWN
                )
            ),

            vol.Required(
                "fog_area_type",
                default=entry.options.get("fog_area_type", entry.data.get("fog_area_type", "normal"))
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        "frequent_dense_fog",
                        "fog_prone",
                        "normal",
                        "rare_fog",
                        "hardly_ever_fog",
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN
                )
            ),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            description_placeholders={
                "general_description": (
                    "Configure your sensor entities for Zambretti Forecast. "
                    "Make sure the selected sensors are active and properly configured in Home Assistant. "
                    "The numerical values below are used to control update intervals and data history."
                )
            },
        )