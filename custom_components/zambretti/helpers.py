import logging

_LOGGER = logging.getLogger(__name__)


def safe_float(value, default=0.0):
    """Safely converts a value to a float, returning a default if conversion fails."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default  # Return default if conversion fails


def alert_desc(alert_level):
    """Get right description with the alert"""

    t_alert_level = safe_float(alert_level)

    messages = {
        0: "🟦 Fine day.",
        1: "🟩 No worries.",
        2: "🟩 Mild day.",
        2.1: "🟩 Mild day. Wind picking up a bit, possibly up to 25kn.",
        2.2: "🟩 Mild day. Wind picking up, possibly up to 30kn.",
        3: "🟨 Caution. Unstable conditions, moderate winds, squalls possible.",
        3.1: "🟨 Caution. Wind picking up, possibly up to 40kn, squalls possible.",
        4: "🟧 Alert! Strong winds, rough seas, storm risk increasing.",
        4.1: "🟧 Alert! Rough seas, storm risk, strong winds possibly up to 50kn.",
        5: "🟥 Alarm! Heavy storm, gale-force winds, dangerous sailing conditions.",
        5.1: "🟥 Alarm! Heavy storm, gale-force winds possibly more than 50kn.",
    }

    return messages.get(t_alert_level, "")
