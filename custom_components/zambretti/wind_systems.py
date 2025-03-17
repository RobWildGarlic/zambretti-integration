"""Regions configuration for Zambretti integration."""

from .helpers import safe_float

import logging
_LOGGER = logging.getLogger(__name__)

# 🌍 Define Geographic Boundaries
REGIONS = {
    # Small reegions forst so they are not ignored for being in a larger region
    "british_isles": (49, 61, -12, 2, "https://en.wikipedia.org/wiki/List_of_local_winds#Europe"),  # UK Met Office (Placed before North Atlantic)
    "western_europe_coast": (35, 50, -10, 5, "https://en.wikipedia.org/wiki/List_of_local_winds#Europe"),  # Meteo France
    #Large regions
    "north_sea_baltic": (50, 65, -5, 30, "https://en.wikipedia.org/wiki/List_of_local_winds#Europe"),  # Danish Meteorological Institute (DMI)
    "mediterranean_northwest": (38, 48, -10, 15, "https://en.wikipedia.org/wiki/List_of_local_winds#Europe"),  # Spain, France, Ligurian Coast
    "mediterranean_southwest": (30, 38, -10, 15, "https://en.wikipedia.org/wiki/List_of_local_winds#Europe"),  # Balearics, Algeria, Tunisia, Western Italy
    "mediterranean_northeast": (38, 48, 15, 40, "https://en.wikipedia.org/wiki/List_of_local_winds#Europe"),  # Adriatic, Greece, Balkans, Turkey
    "mediterranean_southeast": (30, 38, 15, 40, "https://en.wikipedia.org/wiki/List_of_local_winds#Europe"),  # Levant, Cyprus, Egypt, Crete
    "caribbean": (5, 30, -100, -50, "https://en.wikipedia.org/wiki/List_of_local_winds#Caribbean"),  # National Hurricane Center (NOAA)
    "american_east_coast": (25, 50, -85, -60, "https://en.wikipedia.org/wiki/List_of_local_winds#North_America"),  # US National Weather Service
    # Very large regions
    "north_atlantic": (30, 60, -80, 0, ""),  # NOAA Ocean Prediction Center (Placed last)
}
# 🔄 Wind Direction Mapping (region-based)
WIND_SYSTEM_INDEX = {
    "mediterranean_northwest": {
        "N": ["Tramontane", "Mistral"],
        "N-NW": ["Tramontane"],
        "NW": ["Mistral"],
        "W-NW": ["Maestro", "Zephyr"],
        "W": ["Ponente", "Zephyr"],
        "W-SW": ["Libeccio", "Marin"],
        "SW": ["Libeccio"],
        "S-SW": ["Ostro", "Ghibli"],
        "S": ["Ostro", "Khamsin", "Datoo"],
        "S-SE": ["Ghibli", "Sirocco"],
        "SE": ["Levante", "Sirocco"],
        "E-SE": ["Levante", "Sirocco"],
        "E": ["Levante"],
        "E-NE": ["Gregale"],
        "NE": ["Gregale"],
        "N-NE": ["Tramontane"],
    },
    "mediterranean_southwest": {
        "N": ["Mistral"],
        "N-NW": ["Tramontane"],
        "NW": ["Mistral"],
        "W": ["Ponente"],
        "W-SW": ["Libeccio", "Marin"],
        "SW": ["Libeccio"],
        "S-SW": ["Ostro", "Khamsin"],
        "S": ["Ostro", "Ghibli", "Jugo"],
        "S-SE": ["Ghibli", "Sirocco"],
        "SE": ["Sirocco", "Levantadis"],
        "E-SE": ["Sirocco", "Levantadis"],
        "E": ["Sirocco", "Levantadis"],
        "E-NE": ["Gregale"],
        "NE": ["Gregale"],
        "N-NE": ["Tramontane"],
    },
    "mediterranean_northeast": {
        "N": ["Bora", "Meltemi"],
        "N-NW": ["Bora", "Meltemi"],
        "NW": ["Meltemi"],
        "W-NW": ["Maestro"],
        "W": ["Ponente"],
        "W-SW": ["Libeccio"],
        "SW": ["Libeccio"],
        "S-SW": ["Ostro", "Ghibli", "Jugo"],
        "S": ["Ostro", "Khamsin", "Jugo"],
        "S-SE": ["Ghibli", "Jugo", "Sirocco"],
        "SE": ["Levante", "Gregale", "Sirocco", "Levantadis"],
        "E-SE": ["Levante", "Gregale", "Sirocco"],
        "E": ["Levante", "Gregale", "Meltemi", "Levantadis"],
        "E-NE": ["Gregale", "Meltemi", "Bora"],
        "NE": ["Bora", "Meltemi"],
        "N-NE": ["Bora", "Meltemi"],
    },
    "mediterranean_southeast": {
        "N": ["Meltemi"],
        "N-NW": ["Meltemi"],
        "NW": ["Meltemi"],
        "W-NW": ["Maestro"],
        "W": ["Ponente"],
        "W-SW": ["Libeccio"],
        "SW": ["Libeccio"],
        "S-SW": ["Ostro", "Khamsin"],
        "S": ["Ostro", "Ghibli", "Jugo"],
        "S-SE": ["Ghibli", "Sirocco"],
        "SE": ["Sirocco", "Levantadis"],
        "E-SE": ["Sirocco", "Levantadis"],
        "E": ["Gregale", "Levantadis"],
        "E-NE": ["Gregale"],
        "NE": ["Gregale"],
        "N-NE": ["Meltemi"],
    },
    "caribbean": {
        "N": ["El Norte", "Tehuantepecer"],
        "N-NW": ["El Norte"],
        "NW": ["El Norte"],
        "W-NW": [],
        "W": ["Chubasco"],
        "W-SW": ["Chubasco"],
        "SW": [],
        "S-SW": ["Brisas"],
        "S": ["Brisas"],
        "S-SE": ["Brisas"],
        "SE": ["Trade Winds"],
        "E-SE": [],
        "E": ["Trade Winds", "Hurricane Alley"],
        "E-NE": [],
        "NE": ["Trade Winds"],
        "N-NE": []
    },
    "north_atlantic": {
        "N": ["Icelandic Low", "Greenland High", "Arctic Outflow"],
        "N-NE": ["Nor’easters", "Icelandic Low", "Polar Jet Stream"],
        "NE": ["Nor’easters", "Westerlies", "Mid-Latitude Cyclones"],
        "E-NE": ["Azores High", "Trade Winds Influence", "Westerlies"],
        "E": ["Azores High", "Subtropical Westerlies", "Bermuda High Influence"],
        "E-SE": ["Azores High", "Bermuda High", "Trade Winds"],
        "SE": ["Bermuda High", "Trade Winds", "Hurricane Alley"],
        "S-SE": ["Bermuda High", "Azores High", "Tropical Convergence Zone"],
        "S": ["Bermuda High", "Tropical Air Mass", "Hurricane Alley"],
        "S-SW": ["Bermuda High", "Hurricane Influence", "Gulf Stream Influence"],
        "SW": ["Westerlies", "Gulf Stream Influence", "Storm Track"],
        "W-SW": ["Westerlies", "Bermuda High Influence", "Gulf Stream Influence"],
        "W": ["Westerlies", "North Atlantic Drift", "Mid-Latitude Storms"],
        "W-NW": ["Westerlies", "Cold Fronts", "Icelandic Low Influence"],
        "NW": ["Icelandic Low", "Polar Jet Stream", "Greenland High"],
        "N-NW": ["Icelandic Low", "Greenland High", "Arctic Outflow"],
    },
    "british_isles": {
        "N": ["Icelandic Low Influence", "North Sea Storms"],
        "N-NE": ["North Sea Storms", "Easterly Continental Winds"],
        "NE": ["Easterly Continental Winds", "North Sea Storms"],
        "E-NE": ["Easterly Continental Winds", "North Sea Storms"],
        "E": ["Easterly Continental Winds", "Beaufort’s Westerlies"],
        "E-SE": ["Beaufort’s Westerlies", "Southeast Trades"],
        "SE": ["Southeast Trades", "Channel Winds"],
        "S-SE": ["Southeast Trades", "Azores High Influence"],
        "S": ["Azores High Influence", "Channel Winds"],
        "S-SW": ["Channel Winds", "Beaufort’s Westerlies"],
        "SW": ["Beaufort’s Westerlies", "North Atlantic Drift"],
        "W-SW": ["North Atlantic Drift", "Westerlies"],
        "W": ["Westerlies", "North Atlantic Drift"],
        "W-NW": ["Westerlies", "Icelandic Low Influence"],
        "NW": ["Icelandic Low Influence", "North Atlantic Drift"],
        "N-NW": ["Icelandic Low Influence", "North Sea Storms"],
    },
    "western_europe_coast": {
        "N": ["Portuguese Northerlies"],  
        "N-NE": ["Portuguese Northerlies", "Galician Trade Winds"],  
        "NE": ["Galician Trade Winds", "Bay of Biscay Gales"],  
        "E-NE": ["Levanter"],  
        "E": ["Levanter"],  
        "E-SE": ["Levanter", "Iberian Low Pressure Winds"],  
        "SE": ["Iberian Low Pressure Winds"],  
        "S-SE": ["Iberian Low Pressure Winds"],  
        "S": ["Iberian Low Pressure Winds"],  
        "S-SW": ["Iberian Low Pressure Winds"],  
        "SW": ["Bay of Biscay Gales", "Cantabrian Gusts"],  
        "W-SW": ["Brittany Westerlies", "Bay of Biscay Gales"],  
        "W": ["Brittany Westerlies", "Bay of Biscay Gales"],  
        "W-NW": ["Bay of Biscay Gales", "Cantabrian Gusts"],  
        "NW": ["Bay of Biscay Gales", "Portuguese Northerlies"],  
        "N-NW": ["Portuguese Northerlies"],  
    },
    "north_sea_baltic": {
        "N": ["Scandinavian High", "Katabatic Winds"],
        "N-NE": ["Scandinavian High", "Baltic Easterlies"],
        "NE": ["Baltic Easterlies", "Gulf of Finland Wind"],
        "E-NE": ["Baltic Easterlies", "Gulf of Finland Wind", "Danish Straits Winds"],
        "E": ["Baltic Easterlies", "Danish Straits Winds"],
        "E-SE": ["Baltic Easterlies", "Danish Straits Winds"],
        "SE": ["Danish Straits Winds", "Baltic Easterlies", "Skagerrak Gales"],
        "S-SE": ["Danish Straits Winds", "North Sea Westerlies", "Skagerrak Gales"],
        "S": ["North Sea Westerlies", "Skagerrak Gales", "North Atlantic Lows"],
        "S-SW": ["North Sea Westerlies", "North Atlantic Lows"],
        "SW": ["North Sea Westerlies", "North Atlantic Lows"],
        "W-SW": ["North Sea Westerlies", "Skagerrak Gales"],
        "W": ["North Sea Westerlies", "Skagerrak Gales", "North Atlantic Lows"],
        "W-NW": ["North Atlantic Lows", "North Sea Westerlies"],
        "NW": ["North Atlantic Lows", "Scandinavian High"],
        "N-NW": ["Scandinavian High", "Katabatic Winds"],
    },
    "american_east_coast": {
        "N": ["Nor'easters", "Polar Jet Stream", "Great Lakes Outflow"],
        "N-NE": ["Nor'easters", "Great Lakes Outflow"],
        "NE": ["Nor'easters", "Cape Hatteras Cyclones"],
        "E-NE": ["Bermuda High", "Trade Winds"],
        "E": ["Bermuda High", "Trade Winds", "Gulf Stream Winds"],
        "E-SE": ["Bermuda High", "Trade Winds", "Gulf Stream Winds"],
        "SE": ["Bermuda High", "Trade Winds", "Hurricane Alley"],
        "S-SE": ["Bermuda High", "Hurricane Alley", "Coastal Sea Breezes"],
        "S": ["Bermuda High", "Hurricane Alley", "Coastal Sea Breezes"],
        "S-SW": ["Gulf Stream Winds", "Hurricane Alley", "Coastal Sea Breezes"],
        "SW": ["Gulf Stream Winds", "Coastal Sea Breezes"],
        "W-SW": ["Coastal Sea Breezes", "Appalachian Downslope Winds"],
        "W": ["Appalachian Downslope Winds", "Polar Jet Stream"],
        "W-NW": ["Appalachian Downslope Winds", "Great Lakes Outflow"],
        "NW": ["Great Lakes Outflow", "Polar Jet Stream"],
        "N-NW": ["Great Lakes Outflow", "Polar Jet Stream"],
    },
}

# 🌊 Wind System Definitions
WIND_SYSTEM_CATALOG = {
    "Tramontane": ((40, 48, -10, 6), "Dry, strong N wind over Southern France and Spain.", "https://en.wikipedia.org/wiki/Tramontane"),
    "Mistral": ((38, 44, -6, 10), "Cold, dry NW wind, clearing skies in the Western Med.", "https://en.wikipedia.org/wiki/Mistral_(wind)"),
    "Libeccio": ((30, 45, -18, 10), "SW wind, stormy in autumn and winter, high waves.", "https://en.wikipedia.org/wiki/Libeccio"),
    "Sirocco": ((30, 45, -10, 25), "Hot, dusty SE wind, humid near coasts.", "https://en.wikipedia.org/wiki/Sirocco"),
    "Bora": ((38, 48, 12, 20), "Cold NE wind in the Adriatic, sudden strong gusts.", "https://en.wikipedia.org/wiki/Bora_(wind)"),
    "Meltemi": ((34, 48, 20, 30), "Strong summer winds, rough seas, strongest in afternoons.", "https://en.wikipedia.org/wiki/Etesian"),
    "Khamsin": ((25, 38, 20, 35), "Hot, dusty wind from the Sahara, lasts for days.", "https://en.wikipedia.org/wiki/Khamsin"),
    "Gregale": ((30, 42, 12, 25), "Strong NE wind from the Balkans, causes rough seas.", "https://en.wikipedia.org/wiki/Gregale"),
    "Ponente": ((36, 44, -6, 15), "Mild W wind, freshens air and clears skies.", "https://en.wikipedia.org/wiki/West_wind"),
    "Jugo": ((38, 45, 12, 20), "Warm, humid SE wind, bringing storms and rough seas.", "https://en.wikipedia.org/wiki/Sirocco"),
    "Ghibli": ((25, 40, 10, 20), "Intense, hot desert wind, causes sandstorms.", "https://en.wikipedia.org/wiki/Sirocco"),
    "Ostro": ((30, 45, 5, 20), "Warm, humid S wind from Africa, linked to Sirocco.", "https://en.wikipedia.org/wiki/Ostro"),
    "Levantadis": ((35, 42, 18, 28), "Local Levante wind in Ionian and Aegean Seas.", "https://en.wikipedia.org/wiki/Llevantades"),
    "Imbat": ((36, 42, 26, 30), "Cool sea breeze along the Aegean coast.", "https://en.wikipedia.org/wiki/Karşıyaka"),
    "Maestro": ((38, 45, 12, 24), "Gentle NW breeze, pleasant summer weather.", "https://en.wikipedia.org/wiki/Mistral_(wind)#Maestral_or_maestro_in_the_Adriatic"),
    "Zephyr": ((35, 45, -10, 20), "Gentle summer westerly, brings pleasant weather.", "https://en.wikipedia.org/wiki/Mistral_(wind)#Maestral_or_maestro_in_the_Adriatic"),
    "Marin": ((36, 44, -6, 4), "Moist SE wind, heavy rain and storms in Gulf of Lion.", "https://en.wikipedia.org/wiki/Marin_(wind)"),
    "Mbatis": ((35, 42, 20, 30), "Light, refreshing sea breeze common in Greece.", "https://izmir.ktb.gov.tr/EN-239196/general-information.html"),
    "Datoo": ((30, 40, -5, 15), "Hot, dry wind from North Africa, like the Khamsin.", "https://en.wikipedia.org/wiki/Khamsin"),
    "Levante": ((34, 40, -10, 10), "Warm, moist E wind, often brings fog and rain.", "https://en.wikipedia.org/wiki/Levant_(wind)"),
    "Trade Winds": ((5, 30, -90, -55), "Steady NE-E winds, dominant year-round.",""),
    "Brisas": ((10, 25, -90, -55), "Coastal sea breezes, onshore by day, offshore at night.",""),
    "El Norte": ((15, 30, -95, -70), "Strong winter N-NW winds after cold fronts.",""),
    "Chubasco": ((5, 20, -90, -55), "Sudden tropical squalls with gusty winds.",""),
    "Papagayo Winds": ((8, 15, -92, -83), "Strong gap winds blasting from Central America.",""),
    "Tehuantepecer": ((10, 20, -98, -90), "Violent N winds from Mexico, big waves.",""),
    "Hurricane Alley": ((5, 30, -80, -50), "High storm activity, strongest in summer.",""),
    "Westerlies": ((30, 60, -80, 0), "Persistent W winds, strong mid-latitude influence.",""),
    "Nor’easters": ((35, 50, -80, -50), "Intense NE storms along the US East Coast.",""),
    "Bermuda High": ((20, 40, -70, -40), "Stable high pressure steering Atlantic winds.",""),
    "Azores High": ((30, 45, -40, 10), "Affects Europe and North Atlantic weather.",""),
    "Icelandic Low": ((50, 65, -50, -10), "Strong low-pressure system, frequent storms.",""),
    "Greenland High": ((60, 75, -50, -10), "Arctic high pressure, very cold air masses.",""),
    "Trade Winds": ((10, 30, -80, -30), "Persistent tropical E winds.",""),
    "Gulf Stream Influence": ((25, 40, -80, -50), "Warm ocean current, affects storms.",""),
    "Hurricane Alley": ((10, 30, -80, -50), "Common Atlantic hurricane path.",""),
    "Polar Jet Stream": ((45, 70, -80, -10), "Fast-moving upper air current, drives storms.",""),
    "Arctic Outflow": ((60, 75, -80, -10), "Cold air from the Arctic, strong winds.",""),
    "Westerlies": ((48, 61, -15, 5), "Changeable winds across the UK and Ireland.",""),
    "Icelandic Low Influence": ((50, 65, -50, -10), "Drives storms and strong winds in the North Atlantic.",""),
    "Azores High Influence": ((30, 45, -40, 10), "Brings settled weather but can also cause heatwaves.",""),
    "North Atlantic Drift": ((45, 60, -20, 5), "Warm ocean current moderating UK climate.",""),
    "Föhn Effect": ((50, 58, -10, 2), "Warm, dry wind descending in Scotland and NW England.",""),
    "North Sea Storms": ((50, 62, -5, 10), "Sudden squalls, common in autumn and winter.",""),
    "Easterly Continental Winds": ((50, 60, 0, 10), "Cold, dry air from Europe, brings winter snow.",""),
    "Beaufort’s Westerlies": ((48, 60, -15, 5), "Moderate to strong westerlies over the UK.",""),
    "Channel Winds": ((49, 52, -5, 2), "Strong funneling winds in the English Channel.",""),
    "Southeast Trades": ((50, 55, -5, 5), "Warm, humid winds from France, bring mild weather.",""),
    "Portuguese Northerlies": ((35, 44, -10, -5), "Strong summer winds from the north, cooling Portuguese coastal waters.",""),
    "Bay of Biscay Gales": ((43, 50, -10, 0), "Intense storms and strong winds, common in autumn and winter.",""),
    "Galician Trade Winds": ((41, 45, -10, -6), "Persistent NW winds along Galicia, strengthening in summer.",""),
    "Brittany Westerlies": ((47, 50, -8, 2), "Strong westerlies hitting the Breton coast, especially in winter.",""),
    "Iberian Low Pressure Winds": ((35, 45, -10, 0), "Unstable, humid winds driven by low pressure over Spain & Portugal.",""),
    "Levanter": ((35, 37, -7, -5), "Easterly wind in the Strait of Gibraltar, bringing fog & humidity.",""),
    "Cantabrian Gusts": ((42, 45, -10, -2), "Strong local winds on Spain’s N coast, driven by Atlantic storms.",""),
    "North Sea Westerlies": ((50, 65, -5, 10), "Frequent westerly storms and strong gales over the North Sea.",""),
    "Baltic Easterlies": ((53, 65, 10, 30), "Cold & dry in winter, humid & unstable in summer.",""),
    "Katabatic Winds": ((55, 65, 5, 30), "Cold descending winds along Scandinavian coasts.",""),
    "Gulf of Finland Wind": ((58, 61, 20, 30), "Variable winds funneled through narrow Baltic straits.",""),
    "Scandinavian High": ((55, 65, 10, 30), "Cold, dry high-pressure winds from Scandinavia.",""),
    "Skagerrak Gales": ((55, 60, 5, 15), "Strong westerly gales in the Skagerrak Strait.",""),
    "North Atlantic Lows": ((50, 65, -10, 5), "Stormy conditions from low-pressure systems.",""),
    "Danish Straits Winds": ((53, 57, 10, 15), "Rapidly shifting winds through Danish straits.",""),
    "Nor'easters": ((35, 50, -85, -60), "Intense coastal storms with strong winds and heavy rain or snow.",""),
    "Bermuda High": ((20, 40, -80, -50), "Subtropical high-pressure system steering storms & summer heat.",""),
    "Gulf Stream Winds": ((25, 45, -80, -60), "Warm ocean currents fueling storms & moderating temperatures.",""),
    "Hurricane Alley": ((20, 40, -85, -60), "A major track for hurricanes forming in the Atlantic.",""),
    "Appalachian Downslope Winds": ((30, 45, -85, -70), "Gusty, dry winds descending from the Appalachians.",""),
    "Coastal Sea Breezes": ((25, 40, -85, -65), "Daily shifts between land & sea breezes along the coast.",""),
    "Polar Jet Stream": ((35, 50, -90, -60), "Fast-moving air current steering storms & cold outbreaks.",""),
    "Cape Hatteras Cyclones": ((30, 40, -85, -65), "Low-pressure systems intensifying off the Carolina coast.",""),
    "Trade Winds": ((20, 30, -85, -60), "Steady easterly winds steering storms & tropical systems.",""),
    "Great Lakes Outflow": ((40, 50, -85, -70), "Cold air from the Great Lakes fueling snow & strong winds.",""),
}



# 🌍 Default descriptions for wind directions per region
REGION_CATALOG = {
    "mediterranean_northwest": {
        "N": "Northern winds: Cold air from Europe, often strong, affecting France and Northern Spain.",
        "N-NW": "North-Northwest winds: Strong and dry, influenced by Tramontane and Mistral.",
        "NW": "Northwest winds: Mistral-dominated, bringing cold, dry air and clear skies.",
        "W-NW": "West-Northwest winds: Moderate, dry winds, influencing the Gulf of Lion.",
        "W": "West winds: Can bring moisture, sometimes leading to storms and rough seas.",
        "W-SW": "West-Southwest winds: Warm, humid, often stormy, especially near the Gulf of Lion.",
        "SW": "Southwest winds: Can bring storms and high humidity.",
        "S-SW": "South-Southwest winds: Warm and humid, occasionally stormy, affecting Western Italy.",
        "S": "Southern winds: Warmer, sometimes carrying Saharan dust into the region.",
        "S-SE": "South-Southeast winds: Increasing humidity, often mild but unstable.",
        "SE": "Southeasterly winds: Brings moisture, occasional storms near the Ligurian Sea.",
        "E-SE": "East-Southeast winds: Moderate, can bring instability to Northern Italy.",
        "E": "Easterly winds: Brings moisture, less frequent in this region.",
        "E-NE": "East-Northeast winds: Mild but occasionally gusty, affecting the Ligurian coast.",
        "NE": "Northeasterly winds: Can be strong, impacting the Western Italian coast.",
        "N-NE": "North-Northeast winds: Gusty and cold, weaker than in the eastern Mediterranean.",
    },
    "mediterranean_southwest": {
        "N": "Northern winds: Often mild but can bring cooler air into Algeria and Tunisia.",
        "N-NW": "North-Northwest winds: Strong and dry, influenced by the Mistral and Tramontane.",
        "NW": "Northwest winds: Dry, sometimes dusty, affecting the Balearic Islands.",
        "W-NW": "West-Northwest winds: Often moderate, can bring dry air and rough seas.",
        "W": "West winds: Warm, can cause occasional rain and storms in North Africa.",
        "W-SW": "West-Southwest winds: Humid and warm, bringing instability to the region.",
        "SW": "Southwest winds: Can cause storms, particularly in autumn and winter.",
        "S-SW": "South-Southwest winds: Warm and humid, can lead to heavy rain near Tunisia.",
        "S": "Southern winds: Brings Saharan dust and extreme heat, affecting Malta and North Africa.",
        "S-SE": "South-Southeast winds: Mild but can cause high humidity and unstable weather.",
        "SE": "Southeasterly winds: Humid and stormy, often linked to Sirocco.",
        "E-SE": "East-Southeast winds: Can be strong, affecting the western Mediterranean coastline.",
        "E": "Easterly winds: Brings moisture, fog, and occasional rain to the region.",
        "E-NE": "East-Northeast winds: Sometimes gusty, can impact coastal Algeria and Tunisia.",
        "NE": "Northeasterly winds: Moderate winds affecting North Africa and Malta.",
        "N-NE": "North-Northeast winds: Occasionally strong, bringing cooler air inland.",
    },
    "mediterranean_northeast": {
        "N": "Northern winds: Cold, strong gusts, impacting Greece and the Balkans.",
        "N-NW": "North-Northwest winds: Strong and dry, affecting the Adriatic and Aegean Seas.",
        "NW": "Northwest winds: Cool air, often linked to Bora and Meltemi, impacting Greece and Turkey.",
        "W-NW": "West-Northwest winds: Can bring dry air and occasional storms.",
        "W": "West winds: Often moist, bringing rain to the Adriatic and Aegean coasts.",
        "W-SW": "West-Southwest winds: Warm, humid, and sometimes stormy.",
        "SW": "Southwest winds: Stormy conditions, bringing high humidity to coastal areas.",
        "S-SW": "South-Southwest winds: Warm, humid, and sometimes stormy, especially near Greece.",
        "S": "Southern winds: Brings Saharan dust and extreme heat to Greece and Turkey.",
        "S-SE": "South-Southeast winds: Can be mild, but heavy rain possible in the Levant and Aegean.",
        "SE": "Southeasterly winds: Humid and unstable, common in the Ionian and Aegean Seas.",
        "E-SE": "East-Southeast winds: Can be strong and stormy, affecting Greece and Turkey.",
        "E": "Easterly winds: Moist and stormy, linked to Levante, Gregale, and Levantadis.",
        "E-NE": "East-Northeast winds: Can be strong and gusty, bringing cold air, affecting the Aegean.",
        "NE": "Northeasterly winds: Associated with Gregale and Bora, bringing dry, cold air to the Adriatic.",
        "N-NE": "North-Northeast winds: Strong and gusty, associated with Bora and Meltemi.",
    },
    "mediterranean_southeast": {
        "N": "Northern winds: Often mild, but can bring cool air from Turkey.",
        "N-NW": "North-Northwest winds: Can be strong, affecting the Levant and Egypt.",
        "NW": "Northwest winds: Dry air, occasionally stormy, impacting Cyprus and Crete.",
        "W-NW": "West-Northwest winds: Typically moderate, sometimes stormy near the Levant.",
        "W": "West winds: Moist and stormy, can bring significant rainfall to the Middle East.",
        "W-SW": "West-Southwest winds: Warm and humid, occasionally stormy, affecting Israel and Lebanon.",
        "SW": "Southwest winds: Can bring dust storms and unstable weather to the Levant.",
        "S-SW": "South-Southwest winds: Warm, humid, and sometimes stormy, impacting Egypt and Crete.",
        "S": "Southern winds: Brings Saharan dust and heat, affecting Cyprus and the Levant.",
        "S-SE": "South-Southeast winds: Warm, humid, and can bring heavy rain to the Middle East.",
        "SE": "Southeasterly winds: Unstable and stormy, common in the eastern Mediterranean.",
        "E-SE": "East-Southeast winds: Can be strong and stormy, affecting Israel and Cyprus.",
        "E": "Easterly winds: Moist and stormy, linked to Levante, Gregale, and Levantadis.",
        "E-NE": "East-Northeast winds: Can bring cooler air, sometimes strong in coastal Turkey.",
        "NE": "Northeasterly winds: Occasionally strong, affecting Cyprus and the eastern Aegean.",
        "N-NE": "North-Northeast winds: Strong and gusty, occasionally bringing cooler air inland.",
    },
    "caribbean": {
        "N": "Northern winds: Can bring cooler air from North America, often strong in winter.",
        "N-NW": "North-Northwest winds: Typically strong during cold fronts.",
        "NW": "Northwest winds: May be associated with winter storms.",
        "W-NW": "West-Northwest winds: Usually mild, sometimes stormy.",
        "W": "West winds: Can be mild but also stormy, bringing rough seas.",
        "W-SW": "West-Southwest winds: Warm, humid air, increased rain potential.",
        "SW": "Southwest winds: Stormy & wet, often linked to tropical systems.",
        "S-SW": "South-Southwest winds: Can bring warm tropical air, occasionally stormy.",
        "S": "Southern winds: Warm and humid, linked to tropical weather.",
        "S-SE": "South-Southeast winds: Can bring moisture and occasional rain.",
        "SE": "Southeasterly winds: Often warm, humid, sometimes stormy.",
        "E-SE": "East-Southeast winds: Often moderate, sometimes bringing showers.",
        "E": "Easterly winds: Trade Winds dominate, bringing steady conditions.",
        "E-NE": "East-Northeast winds: Often moderate, can be strong in hurricane season.",
        "NE": "Northeasterly winds: Most common Caribbean wind, providing steady weather.",
        "N-NE": "North-Northeast winds: Typically steady but can bring occasional storms.",
    },
    "north_atlantic": {
        "N": "Northern winds: Often cold, stormy, and associated with low pressure. Strong winds from Arctic air masses.",
        "N-NE": "North-Northeast winds: Cold, dry winds often bringing clear skies but low temperatures.",
        "NE": "Northeast winds: Can bring strong storms, heavy precipitation, and Nor’easters along the US East Coast.",
        "E-NE": "East-Northeast winds: Moist winds, often associated with developing storm systems.",
        "E": "Easterly winds: Generally milder, bringing warm oceanic air, but can be humid and unstable.",
        "E-SE": "East-Southeast winds: Warm and humid, can lead to storm formation, particularly in hurricane season.",
        "SE": "Southeast winds: Often wet and stormy, bringing moisture-laden air from the tropics.",
        "S-SE": "South-Southeast winds: Increasing warmth and humidity, precursor to stormy conditions.",
        "S": "Southerly winds: Warm, humid air masses bringing mild but sometimes unstable weather.",
        "S-SW": "South-Southwest winds: Can be stormy in low-pressure systems but often bring milder weather in mid-latitudes.",
        "SW": "Southwest winds: Typically bring mild, wet weather from the Atlantic, influencing Europe’s western coasts.",
        "W-SW": "West-Southwest winds: Mild, damp, and commonly linked with the Westerlies dominating the region.",
        "W": "Westerly winds: The dominant mid-latitude system, bringing frequent changes in weather patterns.",
        "W-NW": "West-Northwest winds: Often cool and dry, following passing storm systems.",
        "NW": "Northwest winds: Cold and dry, often bringing clear but colder weather conditions.",
        "N-NW": "North-Northwest winds: Affected by polar air masses, bringing freezing temperatures and strong gusts.",
    },
    "british_isles": {
        "N": "Strong northern winds bring cold air from the Arctic. Often associated with winter storms, snow, and high winds in Scotland and Northern England.",
        "N-NE": "Chilly northeast winds originate from Scandinavia or Siberia, bringing bitterly cold air in winter, and often leading to snowfall, especially on the east coast.",
        "NE": "Northeasterly winds can bring prolonged damp and cloudy weather, particularly affecting the east of England. In winter, they contribute to freezing conditions and snow showers.",
        "E-NE": "Easterly winds from Europe often bring dry, cold weather in winter and warm, settled conditions in summer. Can cause severe winter snowfall in the east.",
        "E": "Easterly winds carry air from continental Europe. Cold and dry in winter, but can bring heatwaves in summer, leading to uncomfortably warm conditions in the UK.",
        "E-SE": "Southeasterly winds are rare but bring warm, humid air from mainland Europe. In summer, they can lead to heatwaves, while in winter, they may bring freezing rain.",
        "SE": "Warm and moist southeasterly winds bring mild, wet conditions, particularly in autumn and winter, often leading to prolonged rain in the southeast of England.",
        "S-SE": "South-southeast winds originate from the Azores High and can bring extended warm spells in summer, as well as damp and overcast weather in winter.",
        "S": "Southerly winds bring warm air from southern Europe or North Africa. Often lead to mild winters and hot, humid summers. Can increase thunderstorm activity.",
        "S-SW": "South-southwesterly winds are common in the UK and usually bring moist, mild air, resulting in prolonged rain, especially in western regions.",
        "SW": "Southwesterly winds are dominant in the UK, bringing wet and windy conditions, particularly in autumn and winter. They originate from the North Atlantic and contribute to the UK's changeable weather.",
        "W-SW": "Westerly winds bring moisture-laden air from the Atlantic, resulting in frequent rain showers. Strong storms can develop in winter, with powerful gusts along the west coast.",
        "W": "Westerly winds are the prevailing winds in the British Isles, bringing mild, damp weather. The west of the UK experiences heavy rainfall due to these winds, while the east remains drier.",
        "W-NW": "West-northwesterly winds bring cool, fresh air from the Atlantic, often following storms. These winds can bring bright but showery conditions.",
        "NW": "Northwesterly winds bring cold Arctic air, especially in winter, leading to sharp temperature drops, hail showers, and occasional snowfall.",
        "N-NW": "Bitingly cold north-northwesterly winds sweep down from the Arctic, bringing wintry conditions, strong gales, and heavy snow showers to Scotland and Northern England.",
    },
    "north_sea_baltic": {
        "N": "Northern winds: Cold Arctic air from Scandinavia brings freezing temperatures in winter and dry, stable air in summer. Can lead to strong gusts and katabatic winds over coastal areas.",
        "N-NW": "North-Northwest winds: Typically strong and dry, bringing cold conditions in winter. Can create hazardous crosswinds for maritime navigation.",
        "NW": "Northwest winds: Often stormy, particularly in winter, as North Atlantic lows push strong winds into the North Sea. Can bring snow and sleet in colder months.",
        "W-NW": "West-Northwest winds: A common direction in the North Sea, often associated with passing low-pressure systems, bringing frequent rain and rough seas.",
        "W": "Westerly winds: The dominant wind direction, especially in winter. Strong Atlantic-driven storms bring powerful gusts, heavy rain, and rough seas.",
        "W-SW": "West-Southwest winds: Warmer but stormy, with persistent rain and strong gales. Can create dangerous swells and high waves in the North Sea.",
        "SW": "Southwest winds: Mild and humid, bringing prolonged rain and stormy conditions. Frequent in winter, with strong gales affecting coastal regions.",
        "S-SW": "South-Southwest winds: Warm and unstable, bringing stormy weather in winter but milder air in summer. Can be gusty near the Skagerrak Strait.",
        "S": "Southerly winds: Typically warm and moist, but can become unstable. May carry warm air from Europe in summer and stormy conditions in winter.",
        "S-SE": "South-Southeast winds: A mix of warm and unstable air, often leading to fog over the North Sea. In winter, can bring freezing rain or sleet.",
        "SE": "Southeast winds: Baltic influences bring cold air in winter and warm, humid conditions in summer. Can cause dense fog and poor visibility.",
        "E-SE": "East-Southeast winds: Strong Baltic influence, bringing prolonged rain and cold conditions in winter. Can funnel storms into the Danish Straits.",
        "E": "Easterly winds: Dominated by Baltic high pressure in winter, bringing prolonged cold, dry air. In summer, warm but often foggy and humid.",
        "E-NE": "East-Northeast winds: Channeled through the Gulf of Finland and Danish Straits, bringing strong winter chills and heavy snowfall inland.",
        "NE": "Northeast winds: Common in winter, bringing frigid air and snowstorms from Russia. Can cause dangerous ice buildup on ships and coastal flooding.",
        "N-NE": "North-Northeast winds: A mix of cold Arctic air and Baltic winds, bringing strong gales and freezing spray in winter. Can cause extreme wind chills.",
    },
    "american_east_coast": {
        "N": "Northern winds: Cold Arctic air descends from Canada, bringing frigid temperatures in winter and dry, stable air in summer. Can fuel Nor’easters in the Northeast.",
        "N-NW": "North-Northwest winds: Strong cold fronts bring gusty, dry conditions, particularly in winter. Can cause rapid temperature drops and wind chills.",
        "NW": "Northwest winds: Common in winter, bringing **dry, cold Arctic air** from the Great Lakes region. Often follows the passage of strong low-pressure systems.",
        "W-NW": "West-Northwest winds: Cold, dry air from the interior U.S. moves toward the coast, reinforcing high pressure and clearing storms.",
        "W": "Westerly winds: Often mild but variable, associated with the jet stream. Can bring fast-moving storms in winter and **clear, dry conditions** in summer.",
        "W-SW": "West-Southwest winds: A mix of warm, humid air and storm potential. Often carries moisture from the Gulf of Mexico, fueling coastal storms.",
        "SW": "Southwest winds: Brings warm, humid air from the Gulf and Atlantic. Often associated with **tropical storm development and severe thunderstorms**.",
        "S-SW": "South-Southwest winds: Warm and humid, increasing the chance of storms in summer and leading to **foggy, unstable conditions** along the coast.",
        "S": "Southerly winds: **Tropical moisture influence**—can bring high humidity, strong summer storms, and contribute to hurricane strengthening.",
        "S-SE": "South-Southeast winds: Feeds **warm, moist air into storm systems**, increasing rainfall and storm potential. Key wind direction in hurricane formation.",
        "SE": "Southeast winds: Often associated with tropical disturbances and low-pressure systems developing offshore. **Warm, humid, and stormy conditions.**",
        "E-SE": "East-Southeast winds: Brings moisture-laden air from the Atlantic, creating overcast conditions, **fog, and tropical cyclone activity.**",
        "E": "Easterly winds: **Tropical trade winds influence**, often leading to high humidity, summer storms, and **hurricane activity**.",
        "E-NE": "East-Northeast winds: **Nor’easter winds** bring strong gales, heavy rain, and **coastal flooding**, especially in winter.",
        "NE": "Northeast winds: Major **Nor’easter driver**, bringing cold, wet, and stormy weather to the Northeast. Common with powerful winter storms.",
        "N-NE": "North-Northeast winds: Chilly, damp, and **storm-prone**, particularly along the Mid-Atlantic and New England coasts. Drives storm surges inland.",
    },
}

def determine_region(lat, lon):
    """Determine which region a location falls into and return the region name & URL."""
    # A set of coordinates (lat,lon) might land in multiple regions. The REGIONS dictionary
    # is order from small regions to large regions and this function picks the first one.
    # So 'british isles' is picked, not 'north_atlantic' (british_isles are in the north_atlantic).
    for region, values in REGIONS.items():
        lat_min, lat_max, lon_min, lon_max, url = values  # ✅ Correct unpacking
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            _LOGGER.debug(f"✅ Location ({lat}, {lon}) identified as {region}, url {url}.")
            return region, url
    return "unknown", "none"

def wind_systems(region, region_url, latitude, longitude, wind_direction, wind_speed):
    """Determine the most relevant wind system based on region, wind direction, and location."""
    
    _LOGGER.debug(f"WIND_SYSTEMS: {region}  {region_url}")
    default_description = REGION_CATALOG.get(region, {}).get(wind_direction, "No wind description available.")

    region_name = region.replace("_", " ").title() 
    default_url = f'<a href="{region_url}">{region_name}</a>'
    _LOGGER.debug(f"WIND_SYSTEMS: {default_url}")
    
    # ✅ Step 1: Handle low wind speeds
    if safe_float(wind_speed) < 5:
        _LOGGER.debug("Wind speed < 5, so default description applies.")
        return f"No wind, so {default_description}", default_url

    wind_systems_for_region = []
    # ✅ Step 2: Get possible wind systems based on wind direction
    if region in WIND_SYSTEM_INDEX and wind_direction in WIND_SYSTEM_INDEX[region]:
        wind_systems_for_region = WIND_SYSTEM_INDEX[region][wind_direction]
        _LOGGER.debug(f"🌬 Possible wind systems for {wind_direction} in {region}: {wind_systems_for_region}")
    else:
        _LOGGER.warning(f"⚠️ No wind systems found for {wind_direction} in {region}.")
    
    # ✅ Step 3: If no wind system found, return the default description
    if not wind_systems_for_region:
        return f"No systems in region, so {default_description}", default_url
    
    # ✅ Step 4: Check which wind systems apply based on coordinates
    descriptions = []
    urls = []
    for wind_system in wind_systems_for_region:
        if wind_system in WIND_SYSTEM_CATALOG:
            bounds, system_desc, system_url = WIND_SYSTEM_CATALOG[wind_system]  # Extract bounds & description
            lat_min, lat_max, lon_min, lon_max = bounds  # Unpack bounds
            
            _LOGGER.debug(f"Checking {wind_system}: Bounds {bounds} for location ({latitude}, {longitude})")
            
            # Check if the coordinates fall within the wind system's bounds
            if lat_min <= latitude <= lat_max and lon_min <= longitude <= lon_max:
                descriptions.append(f"{wind_system}: {system_desc}")  # ✅ Valid wind system for this location
                urls.append(f'<a href="{system_url}">{wind_system}</a>')
                _LOGGER.debug(f"✅ Match: <a href=\"{system_url}\">{wind_system}</a>")
                
    # ✅ Step 5: If matching wind systems found, return them
    if descriptions:
        _LOGGER.info(f"✅ Matching wind systems: {descriptions}")
        urls.append(default_url)
        return "\n".join(descriptions), " ".join(urls)  # Return the matched wind systems
    
    _LOGGER.warning(f"⚠️ No specific wind system found for {wind_direction} in {region}. Using default with {default_url}")

    # ✅ Step 6: Return default wind description if no specific wind system applies
    return default_description, default_url