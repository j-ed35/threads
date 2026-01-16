import requests
from datetime import datetime
from .config import Config


class NBAClient:
    def __init__(self):
        self.api_key = Config.NBA_API_KEY
        self.alerts_api_key = Config.NBA_ALERTS_API_KEY
        self.standings_key = Config.NBA_STANDINGS_KEY
        self.query_tool_key = Config.QUERY_TOOL_API_KEY
        self.stats_key = Config.STATS_API_KEY
        self.base_url = Config.NBA_API_BASE

    def get_todays_games(self):
        """Fetch today's NBA games"""
        # Get current season (e.g., "2025-26")
        now = datetime.now()
        current_year = now.year
        current_month = now.month

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
        url = f"{self.base_url}/api/standings/league"
        headers = {"X-NBA-Api-Key": self.standings_key}
        params = {
            "leagueId": Config.LEAGUE_ID,
            "season": season,
            "seasonType": season_type,
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        return response.json()

    def get_top_teams_by_stat(
        self, stat_name: str, limit: int = 10, season_year: str = "2025-26"
    ) -> dict:
        """
        Get top teams for a specific stat category.

        Args:
            stat_name: Stat to rank by (e.g., "BASE_PTS", "BASE_FG_PCT", "BASE_AST", "ADV_TM_DEF_RATING")
            limit: Number of teams to return (default 10)
            season_year: Season (e.g., "2025-26")

        Returns:
            API response with top teams sorted by the specified stat
        """
        url = f"{self.base_url}/api/querytool/season/team"
        headers = {"X-NBA-Api-Key": self.query_tool_key}

        # Import here to avoid circular dependency
        from .rankings import RankingsChecker

        # Use the response key for sortColumn (e.g., "OPP_PTS_PG" for "OPP_PTS")
        # If no mapping exists, extract the stat name (e.g., "PTS" from "BASE_PTS")
        sort_stat = RankingsChecker.TEAM_STAT_RESPONSE_KEYS.get(
            stat_name, stat_name.split("_", 1)[-1] if "_" in stat_name else stat_name
        )

        # Check if this stat should be sorted ascending (lower is better)
        sort_order = (
            "ASC" if stat_name in RankingsChecker.TEAM_STATS_ASCENDING else "DESC"
        )

        params = {
            "measures": stat_name,
            "leagueId": Config.LEAGUE_ID,
            "seasonYear": season_year,
            "seasonType": "Regular Season",
            "perMode": "PerGame",
            "Grouping": "None",
            "sortColumn": f"{sort_stat}|{sort_order}",
            "MaxRowsReturned": limit,
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch team stats for {stat_name}: {e}")

    def get_top_players_by_stat(
        self,
        stat_category: str,
        limit: int = 10,
        season_year: str = "2025-26",
        per_mode: str = "PerGame",
    ) -> dict:
        """
        Get top players for a specific stat category using the official leaders endpoint.

        Args:
            stat_category: Stat category (e.g., "PTS", "AST", "REB", "FG_PCT")
            limit: Number of players to return (default 10)
            season_year: Season (e.g., "2025-26")
            per_mode: Stats mode - "PerGame", "Totals", or "Per48"

        Returns:
            API response with top players for the specified stat
        """
        url = f"{self.base_url}/api/stats/player/leaders/official"
        headers = {"X-NBA-Api-Key": self.stats_key}
        params = {
            "leagueId": Config.LEAGUE_ID,
            "season": season_year,
            "seasonType": "Regular Season",
            "statCategory": stat_category,
            "perMode": per_mode,
            "topX": limit,
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch player leaders for {stat_category}: {e}")

    def get_query_players_by_stat(
        self, stat_name: str, limit: int = 10, season_year: str = "2025-26"
    ) -> dict:
        """
        Get top players for a specific stat category using the Query tool instead of official leaders.

        Args:
            stat_name: Stat to rank by (e.g., "BASE_PTS", "BASE_FG_PCT", "BASE_AST", "ADV_TM_DEF_RATING")
            limit: Number of players to return (default 10)
            season_year: Season (e.g., "2025-26")

        Returns:
            API response with top players sorted by the specified stat
        """
        url = f"{self.base_url}/api/querytool/season/player"
        headers = {"X-NBA-Api-Key": self.query_tool_key}

        from .rankings import RankingsChecker

        sort_stat = RankingsChecker.TEAM_STAT_RESPONSE_KEYS.get(
            stat_name, stat_name.split("_", 1)[-1] if "_" in stat_name else stat_name
        )

        # Check if this stat should be sorted ascending (lower is better)
        sort_order = (
            "ASC" if stat_name in RankingsChecker.TEAM_STATS_ASCENDING else "DESC"
        )

        params = {
            "measures": stat_name,
            "leagueId": Config.LEAGUE_ID,
            "seasonYear": season_year,
            "seasonType": "Regular Season",
            "perMode": "Totals",
            "Grouping": "None",
            "sortColumn": f"{sort_stat}|{sort_order}",
            "MaxRowsReturned": limit,
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch team stats for {stat_name}: {e}")
