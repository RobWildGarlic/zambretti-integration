import logging

from .dictionaries import REGIONS

_LOGGER = logging.getLogger(__name__)


def determine_region(lat, lon):
    """Determine which region a location falls into and return the region name & URL."""
    # A set of coordinates (lat,lon) might land in multiple regions. The REGIONS dictionary
    # is order from small regions to large regions and this function picks the first one.
    # So 'british isles' is picked, not 'north_atlantic' (british_isles are in the north_atlantic).

    for region, values in REGIONS.items():
        lat_min, lat_max, lon_min, lon_max, url = values  # ✅ Correct unpacking
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            region_name = region.replace("_", " ")
            if region_name:
                region_name = region_name[0].upper() + region_name[1:]
            _LOGGER.debug(
                f"✅ Location ({lat}, {lon}) identified as {region}, url {url}."
            )
            return region, region_name, url
    _LOGGER.debug(f"✅ Location ({lat}, {lon}) no region.")
    return "unknown", "unknown", "none"
