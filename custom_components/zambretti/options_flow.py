import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector
from .const import DOMAIN, DEFAULT_PRESSURE_HISTORY_HOURS, DEFAULT_UPDATE_INTERVAL_MINUTE

class ZambrettiOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Zambretti options flow for modifying settings after setup."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema({
            vol.Required("wind_direction_sensor", default=self.config_entry.options.get("wind_direction_sensor", self.config_entry.data.get("wind_direction_sensor", ""))): 
                selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
            vol.Required("wind_speed_sensor_knots", default=self.config_entry.options.get("wind_speed_sensor_knots", self.config_entry.data.get("wind_speed_sensor_knots", ""))): 
                selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
            vol.Required("atmospheric_pressure_sensor", default=self.config_entry.options.get("atmospheric_pressure_sensor", self.config_entry.data.get("atmospheric_pressure_sensor", ""))): 
                selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
            vol.Required("temperature_sensor", default=self.config_entry.options.get("temperature_sensor", self.config_entry.data.get("temperature_sensor", ""))): 
                selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
            vol.Required("humidity_sensor", default=self.config_entry.options.get("humidity_sensor", self.config_entry.data.get("humidity_sensor", ""))): 
                selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
			vol.Required("device_tracker_home",  default=self.config_entry.options.get("device_tracker_home", self.config_entry.data.get("device_tracker_home", ""))):
                selector.EntitySelector(
			        selector.EntitySelectorConfig(domain="device_tracker")
			    ),
            vol.Required("update_interval_minutes", default=self.config_entry.options.get("update_interval_minutes", self.config_entry.data.get("update_interval_minutes",5))): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["1", "5", "10", "15", "20", "30", "60"],
                    mode=selector.SelectSelectorMode.DROPDOWN
                )
            ),            
            vol.Required("pressure_history_hours", default=self.config_entry.options.get("pressure_history_hours", self.config_entry.data.get("pressure_history_hours",3))): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["3", "6", "9", "12"],
                    mode=selector.SelectSelectorMode.DROPDOWN
                )
            ),            
            vol.Required("fog_area_type", default=self.config_entry.options.get("fog_area_type", self.config_entry.data.get("fog_area_type", "normal"))): 
                selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            "frequent_dense_fog",
                            "fog_prone",
                            "normal",
                            "rare_fog",
                            "hardly_ever_fog"
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
            }
        )