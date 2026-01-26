# Mapping of NBA API broadcaster names to Slack emoji names
BROADCASTER_EMOJI_MAP = {
    "NBA TV": "NBATV",
    "ESPN": "ESPN",
    "TNT": "TNT",
    "ABC": "ABC",
    "Prime Video": "PrimeVideo",
    "Peacock": "peacock",
    "NBC": "nbc_peacock",
}


def get_broadcaster_emoji(broadcaster_name):
    """Convert broadcaster display name to Slack emoji format"""
    emoji_name = BROADCASTER_EMOJI_MAP.get(
        broadcaster_name, broadcaster_name.replace(" ", "")
    )
    return f":_{emoji_name}:"


PLAYERS_EXCLUDED = {"Terry Rozier", "Jayson Tatum"}
