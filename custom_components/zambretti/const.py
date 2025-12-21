import logging
#=============================================================================

DOMAIN = "zambretti"
Z_DEBUG = False
Z_PERF = True

DEFAULT_UPDATE_INTERVAL_MINUTE = 10
DEFAULT_PRESSURE_HISTORY_HOURS = 3


#=============================================================================

ICON_MAPPING = [
    ('mdi:weather-sunny','mdi:weather-night'),
    ('mdi:weather-partly-cloudy', 'mdi:weather-night-partly-cloudy'),
    ('mdi:weather-partly-rainy','mdi:weather-partly-rainy'),
    ('mdi:weather-cloudy','mdi:weather-cloudy'),
    ('mdi:weather-rainy','mdi:weather-rainy'),
    ('mdi:weather-pouring','mdi:weather-pouring'),
    ('mdi:weather-lightning-rainy','mdi:weather-lightning-rainy'),
    ('mdi:weather-windy','mdi:weather-windy'),
    ('mdi:weather-hurricane-outline','mdi:weather-hurricane-outline')
]



