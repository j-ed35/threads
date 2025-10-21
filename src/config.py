import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    NBA_API_KEY = os.getenv("NBA_API_KEY")
    NBA_API_BASE = "https://api.nba.com/v0"
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    ED_TEST_WEBHOOK_URL = os.getenv("ED_TEST_WEBHOOK_URL")
    LEAGUE_ID = "00"  # NBA

    @classmethod
    def validate(cls):
        """Validate that required config is present"""
        if not cls.NBA_API_KEY:
            raise ValueError("NBA_API_KEY not found in environment")
        if not cls.SLACK_WEBHOOK_URL:
            raise ValueError("SLACK_WEBHOOK_URL not found in environment")
