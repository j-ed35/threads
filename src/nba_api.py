import requests
from datetime import datetime
from .config import Config


class NBAClient:
    def __init__(self):
        self.api_key = Config.NBA_API_KEY
        self.alerts_api_key = Config.NBA_ALERTS_API_KEY
        self.base_url = Config.NBA_API_BASE

    def get_todays_games(self):
        """Fetch today's NBA games"""
        # Get current season (e.g., "2025-26")
        current_year = datetime.now().year
        current_month = datetime.now().month

        if current_month >= 10:
            season = f"{current_year}-{str(current_year + 1)[-2:]}"
        else:  # Before October
            season = f"{current_year - 1}-{str(current_year)[-2:]}"

        url = f"{self.base_url}/api/schedule/full"
        headers = {"X-NBA-Api-Key": self.api_key}
        params = {
            "leagueId": Config.LEAGUE_ID,
            "season": season,
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch NBA games: {e}")

    def get_pregame_storylines(self, game_id, storyline_count=10):
        """Fetch pregame storylines for a specific game"""
        url = f"{self.base_url}/api/alerts/topNPregameStorylines"
        headers = {"X-NBA-Api-Key": self.alerts_api_key}
        params = {
            "gameId": game_id,
            "storylineCount": min(storyline_count, 10),  # Cap at API max of 10
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Return empty list on error so we don't break the entire schedule
            print(f"Warning: Failed to fetch storylines for game {game_id}: {e}")
            return []

    def get_team_standings(
        self, season: str = "2025-26", season_type: str = "Regular Season"
    ) -> dict:
        """
        Fetch league standings data.

        Args:
            season: Season year (e.g., "2025-26")
            season_type: Type of season ("Regular Season", "Pre Season", etc.)

        Returns:
            Dictionary containing standings data
        """
        url = f"{Config.NBA_API_BASE}/api/standings/league"

        headers = {"X-NBA-Api-Key": Config.NBA_STANDINGS_KEY}

        params = {
            "leagueId": Config.LEAGUE_ID,
            "season": season,
            "seasonType": season_type,
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        return response.json()
