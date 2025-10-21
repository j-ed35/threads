import requests
from datetime import datetime
from .config import Config


class NBAClient:
    def __init__(self):
        self.api_key = Config.NBA_API_KEY
        self.base_url = Config.NBA_API_BASE

    def get_todays_games(self):
        """Fetch today's NBA games"""
        today = datetime.now().strftime("%Y-%m-%d")

        url = f"{self.base_url}/api/schedule/rolling"
        headers = {"X-NBA-Api-Key": self.api_key}
        params = {"leagueId": Config.LEAGUE_ID, "gameDate": today}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch NBA games: {e}")
