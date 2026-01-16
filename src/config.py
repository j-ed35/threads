import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # NBA API Keys
    NBA_API_KEY = os.getenv("NBA_API_KEY")
    NBA_ALERTS_API_KEY = os.getenv("NBA_ALERTS_API_KEY")
    NBA_STANDINGS_KEY = os.getenv("NBA_STANDINGS_KEY")
    QUERY_TOOL_API_KEY = os.getenv("QUERY_TOOL_API_KEY")
    STATS_API_KEY = os.getenv("STATS_API_KEY")
    NBA_API_BASE = "https://api.nba.com/v0"
    LEAGUE_ID = "00"  # NBA

    # Slack OAuth Configuration
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

    # Slack Channel IDs
    SLACK_CHANNEL_ID_ED_TESTING = os.getenv("SLACK_CHANNEL_ID_ED_TESTING")
    SLACK_CHANNEL_ID_DAILY_THREADS = os.getenv("SLACK_CHANNEL_ID_DAILY_THREADS")
    SLACK_CHANNEL_ID_MOOKIE = os.getenv("SLACK_CHANNEL_ID_MOOKIE")

    # Legacy webhook URLs (kept for backwards compatibility)
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    ED_TEST_WEBHOOK_URL = os.getenv("ED_TEST_WEBHOOK_URL")
    SLACKHOOK2_URL = os.getenv("SLACKHOOK2_URL")

    @classmethod
    def validate(cls, require_nba_key=True):
        """Validate that required config is present"""
        if require_nba_key and not cls.NBA_API_KEY:
            raise ValueError("NBA_API_KEY not found in environment")
        if not cls.NBA_ALERTS_API_KEY:
            raise ValueError("NBA_ALERTS_API_KEY not found in environment")
        if not cls.QUERY_TOOL_API_KEY:
            raise ValueError("QUERY_TOOL_API_KEY not found in environment")
        if not cls.STATS_API_KEY:
            raise ValueError("STATS_API_KEY not found in environment")

        # Validate Slack OAuth configuration
        if not cls.SLACK_BOT_TOKEN:
            raise ValueError("SLACK_BOT_TOKEN not found in environment")
        if not cls.SLACK_CHANNEL_ID_DAILY_THREADS:
            raise ValueError("SLACK_CHANNEL_ID_DAILY_THREADS not found in environment")
