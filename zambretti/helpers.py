import logging
_LOGGER = logging.getLogger(__name__)

def safe_float(value, default=0.0):
    """Safely converts a value to a float, returning a default if conversion fails."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default  # Return default if conversion fails

def alert_desc(alert_level):
    """Get right description with the alert """
    
    t_alert_level = safe_float(alert_level)
    
    if t_alert_level == 0:
        return "🟦 Fine day."
    elif t_alert_level == 1:
        return "🟩 No worries."
    elif t_alert_level == 2:
        return "🟩 Mild day."
    elif t_alert_level == 2.1:
        return "🟩 Mild day. Wind picking up a bit, possibly up to 25kn."
    elif t_alert_level == 2.2:
        return "🟩 Mild day. Wind picking up, possibly up to 30kn."
    elif t_alert_level == 3:
        return "🟨 Caution. Unstable conditions, moderate winds, squalls possible."
    elif t_alert_level == 3.1:
        return "🟨 Caution. Wind picking up, possibly up to 40kn, squalls possible."
    elif t_alert_level == 4:
        return "🟧 Alert! Strong winds, rough seas, storm risk increasing."
    elif t_alert_level == 4.1:
        return "🟧 Alert! Rough seas, storm risk, strong winds possibly up to 50kn."
    elif t_alert_level == 5:
        return "🟥 Alarm! Heavy storm, gale-force winds, dangerous sailing conditions."
    elif t_alert_level == 5.1:
        return "🟥 Alarm! Heavy storm, gale-force winds possibly more than 50kn."
    else:
        return ""  # Explicitly return an empty string for unknown levels    
    
