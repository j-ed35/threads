import os
from dataclasses import dataclass
from datetime import date

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class ChannelSettings:
    include_injuries: bool
    include_milestones: bool


# #ed-testing reuses this exact object so it stays a 1:1 mirror of #daily-threads.
DAILY_THREADS = ChannelSettings(include_injuries=False, include_milestones=False)
MOOKIE_BLAYLOCK = ChannelSettings(include_injuries=True, include_milestones=True)

# channel name -> (env var holding the channel ID, settings)
CHANNELS = {
    "#daily-threads": ("SLACK_CHANNEL_ID_NBA_DAILY_THREADS", DAILY_THREADS),
    "#ed-testing": ("SLACK_CHANNEL_ID_ED_TESTING", DAILY_THREADS),
    "#Mookie-Blaylock": ("SLACK_CHANNEL_ID_MOOKIE_BLAYLOCK", MOOKIE_BLAYLOCK),
}


def season_for(d: date) -> str:
    """NBA season string for a date, e.g. 2026-10-19 -> "2026-27", 2026-03-21 -> "2025-26"."""
    y = d.year
    return f"{y}-{str(y + 1)[2:]}" if d.month >= 10 else f"{y - 1}-{str(y)[2:]}"


class Config:
    NBA_API_KEY = os.getenv("NBA_API_KEY")
    NBA_ALERTS_API_KEY = os.getenv("NBA_ALERTS_API_KEY")
    NBA_STANDINGS_KEY = os.getenv("NBA_STANDINGS_KEY")
    QUERY_TOOL_API_KEY = os.getenv("QUERY_TOOL_API_KEY")
    STATS_API_KEY = os.getenv("STATS_API_KEY")
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
    NBA_API_BASE = "https://api.nba.com/v0"
    LEAGUE_ID = "00"  # NBA

    # Keys a threads run calls with.
    REQUIRED_KEYS = (
        "NBA_API_KEY",
        "NBA_STANDINGS_KEY",
        "QUERY_TOOL_API_KEY",
        "STATS_API_KEY",
        "SLACK_BOT_TOKEN",
    )

    @staticmethod
    def validate(channel_env: str = None, keys=REQUIRED_KEYS):
        """Raise if any required key, or the channel being posted to, is unset."""
        missing = [k for k in (*keys, channel_env) if k and not os.getenv(k)]
        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")

    @staticmethod
    def channel(name: str, keys=REQUIRED_KEYS) -> tuple:
        """Validate config and return (channel_id, settings) for a channel name in CHANNELS."""
        env_var, settings = CHANNELS[name]
        Config.validate(env_var, keys)
        return os.getenv(env_var), settings
