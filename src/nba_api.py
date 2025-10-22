import requests
from datetime import datetime
from .config import Config


class NBAClient:
    def __init__(self):
        self.api_key = Config.NBA_API_KEY
        self.base_url = Config.NBA_API_BASE

    def get_todays_games(self):
        """Fetch today's NBA games"""
        # Get current season (e.g., "2025-26")
        current_year = datetime.now().year
        current_month = datetime.now().month

        # NBA season spans two years, starting in October
        if current_month >= 10:  # October or later
            season = f"{current_year}-{str(current_year + 1)[-2:]}"
        else:  # Before October
            season = f"{current_year - 1}-{str(current_year)[-2:]}"

        url = f"{self.base_url}/api/schedule/full"
        headers = {"X-NBA-Api-Key": self.api_key}
        params = {
            "leagueId": Config.LEAGUE_ID,
            "season": season,
            # Note: No gameDate parameter - we get the full season and filter in formatter
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch NBA games: {e}")
