import threading

import requests

from .config import Config


class NBAClient:
    """Thin wrapper over api.nba.com. Every request goes through _get so calls are counted."""

    call_count = 0
    _count_lock = threading.Lock()

    def __init__(self):
        self.session = requests.Session()

    def _get(self, path: str, key: str, params: dict, timeout: int = 15) -> dict:
        with NBAClient._count_lock:
            NBAClient.call_count += 1
        response = self.session.get(
            f"{Config.NBA_API_BASE}{path}",
            headers={"X-NBA-Api-Key": key},
            params=params,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_schedule(self, season: str) -> dict:
        return self._get(
            "/api/schedule/full",
            Config.NBA_API_KEY,
            {"leagueId": Config.LEAGUE_ID, "season": season},
        )

    def get_standings(self, season: str) -> dict:
        return self._get(
            "/api/standings/league",
            Config.NBA_STANDINGS_KEY,
            {
                "leagueId": Config.LEAGUE_ID,
                "season": season,
                "seasonType": "Regular Season",
            },
        )

    def get_injuries(self) -> dict:
        return self._get(
            "/api/stats/injury", Config.STATS_API_KEY, {"leagueId": Config.LEAGUE_ID}
        )

    def get_team_roster(self, team_id, season: str) -> list:
        data = self._get(
            "/api/stats/team/roster",
            Config.STATS_API_KEY,
            {"leagueId": Config.LEAGUE_ID, "season": season, "teamId": team_id},
        )
        return data.get("players", [])

    def get_top_teams(
        self, measure: str, sort_col: str, ascending: bool, season: str, limit: int = 10
    ) -> list:
        data = self._get(
            "/api/querytool/season/team",
            Config.QUERY_TOOL_API_KEY,
            {
                "measures": measure,
                "leagueId": Config.LEAGUE_ID,
                "seasonYear": season,
                "seasonType": "Regular Season",
                "perMode": "PerGame",
                "Grouping": "None",
                "sortColumn": f"{sort_col}|{'ASC' if ascending else 'DESC'}",
                "MaxRowsReturned": limit,
            },
        )
        return data.get("teams", [])

    def get_top_players(self, stat_category: str, season: str, limit: int = 10) -> list:
        data = self._get(
            "/api/stats/player/leaders/official",
            Config.STATS_API_KEY,
            {
                "leagueId": Config.LEAGUE_ID,
                "season": season,
                "seasonType": "Regular Season",
                "statCategory": stat_category,
                "perMode": "PerGame",
                "topX": limit,
            },
        )
        # Before a season has games, this endpoint silently returns the previous season.
        if data.get("season", season) != season:
            return []
        return data.get("players", [])

    def get_career_leaders(
        self, measure: str, sort_col: str, rows: int, season_endpoint: bool = False
    ) -> list:
        """
        All-time regular-season career totals, in rank order.

        season_endpoint=True uses /querytool/season/player with SeasonYear=All, which also
        returns career totals and carries stats (DD2, TD3) the career endpoint lacks.
        """
        path = "season" if season_endpoint else "career"
        data = self._get(
            f"/api/querytool/{path}/player",
            Config.QUERY_TOOL_API_KEY,
            {
                "Measures": measure,
                "LeagueId": Config.LEAGUE_ID,
                "SeasonYear": "All",
                "SeasonType": "Regular Season",
                "Grouping": "None",
                "TeamGrouping": "N",
                "PerMode": "Totals",
                "SortColumn": f"{sort_col}|DESC",
                "MaxRowsReturned": rows,
            },
        )
        return data.get("players", [])
