# src/rankings.py
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from .nba_api import NBAClient


class RankingsChecker:
    """Handles fetching and checking NBA rankings for teams and players"""

    # Stats where lower values are better (sorted ascending)
    TEAM_STATS_ASCENDING = {
        "ADV_TM_DEF_RATING",  # Lower defensive rating is better
        "OPP_PTS",  # Lower opponent points is better
    }

    # Stat groupings for display formatting
    TEAM_STAT_GROUPS = {
        "basic": [
            "BASE_PTS",
            "BASE_FG_PCT",
            "BASE_FG3_PCT",
            "BASE_AST",
            "BASE_REB",
            "BASE_STL",
            "BASE_BLK",
            "OPP_PTS",
        ],
        "advanced": ["ADV_TM_NET_RATING", "ADV_TM_OFF_RATING", "ADV_TM_DEF_RATING"],
    }

    # Friendly names for stats
    TEAM_STAT_NAMES = {
        "BASE_PTS": "PPG",
        "BASE_FG_PCT": "FG%",
        "BASE_FG3_PCT": "3P%",
        "BASE_AST": "AST",
        "BASE_REB": "REB",
        "BASE_STL": "STL",
        "BASE_BLK": "BLK",
        "ADV_TM_NET_RATING": "Net RTG",
        "ADV_TM_OFF_RATING": "Off RTG",
        "ADV_TM_DEF_RATING": "Def RTG",
        "OPP_PTS": "Opp PPG",
    }

    # Mapping from request stat to API response stat key
    TEAM_STAT_RESPONSE_KEYS = {
        "BASE_PTS": "PTS_PG",
        "BASE_FG_PCT": "FG_PCT",
        "BASE_FG3_PCT": "FG3_PCT",
        "BASE_AST": "AST_PG",
        "BASE_REB": "REB_PG",
        "BASE_STL": "STL_PG",
        "BASE_BLK": "BLK_PG",
        "ADV_TM_NET_RATING": "TM_NET_RATING",
        "ADV_TM_OFF_RATING": "TM_OFF_RATING",
        "ADV_TM_DEF_RATING": "TM_DEF_RATING",
        "OPP_PTS": "OPP_PTS_PG",
    }

    PLAYER_STAT_NAMES = {
        "PTS": "PPG",
        "AST": "APG",
        "REB": "RPG",
        "STL": "SPG",
        "BLK": "BPG",
        "FG_PCT": "FG%",
        "FG3M": "3PM",
        "FG3_PCT": "3P%",
    }

    # Map stat names to their API response keys (lowercase)
    PLAYER_STAT_RESPONSE_KEYS = {
        "PTS": "pts",
        "AST": "ast",
        "REB": "reb",
        "STL": "stl",
        "BLK": "blk",
        "FG_PCT": "fgPct",
        "FG3M": "fg3m",
        "FG3_PCT": "fg3Pct",
    }

    # Map our stat names to the API's statCategory parameter
    PLAYER_STAT_API_CATEGORIES = {
        "PTS": "PTS",
        "AST": "AST",
        "REB": "REB",
        "STL": "STL",
        "BLK": "BLK",
        "FG_PCT": "FG_PCT",
        "FG3M": "FG3M",
        "FG3_PCT": "FG3_PCT",
    }

    def __init__(self):
        self.client = NBAClient()
        self.team_stats = list(self.TEAM_STAT_NAMES.keys())
        self.player_stats = list(self.PLAYER_STAT_NAMES.keys())
        # Index for O(1) team lookups: team_id -> {stat: rank_info}
        self._team_rankings_index = None
        # Index for O(1) player lookups by team: team_tricode -> [player_rank_info, ...]
        self._player_rankings_by_team = None

    def _fetch_team_stat(self, stat: str, season_year: str) -> tuple:
        """Fetch a single team stat. Returns (stat_name, teams_list)."""
        try:
            response = self.client.get_top_teams_by_stat(
                stat, limit=10, season_year=season_year
            )
            teams_data = response.get("teams", [])
            response_stat_key = self.TEAM_STAT_RESPONSE_KEYS.get(stat, stat)

            teams = []
            for rank, team in enumerate(teams_data, start=1):
                teams.append(
                    {
                        "teamId": str(team.get("teamId")),
                        "teamName": team.get("teamName", ""),
                        "teamTricode": team.get("teamTricode", ""),
                        "rank": rank,
                        "value": team.get("stats", {}).get(response_stat_key, 0),
                    }
                )
            return (stat, teams)
        except Exception:
            return (stat, [])

    def _fetch_player_stat(self, stat: str, season_year: str) -> tuple:
        """Fetch a single player stat. Returns (stat_name, players_list)."""
        try:
            api_stat_category = self.PLAYER_STAT_API_CATEGORIES.get(stat, stat)
            response = self.client.get_top_players_by_stat(
                api_stat_category,
                limit=10,
                season_year=season_year,
            )
            players_data = response.get("players", [])
            stat_key = self.PLAYER_STAT_RESPONSE_KEYS.get(stat, stat.lower())

            players = []
            for player in players_data[:10]:
                players.append(
                    {
                        "playerId": str(player.get("personId", "")),
                        "playerName": player.get("name", ""),
                        "teamTricode": player.get("teamAbbreviation", ""),
                        "rank": player.get("rank", 0),
                        "value": player.get(stat_key, 0),
                    }
                )
            return (stat, players)
        except Exception:
            return (stat, [])

    def get_all_top_teams(self, season_year: str = "2025-26") -> Dict[str, List[dict]]:
        """
        Fetch top 10 teams for all tracked stats using parallel API calls.

        Returns:
            Dict mapping stat name to list of team dicts with rank info
        """
        rankings = {}

        # Use ThreadPoolExecutor for parallel API calls
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self._fetch_team_stat, stat, season_year): stat
                for stat in self.team_stats
            }
            for future in as_completed(futures):
                stat, teams = future.result()
                rankings[stat] = teams

        # Build index for O(1) lookups
        self._build_team_rankings_index(rankings)

        return rankings

    def get_all_top_players(
        self, season_year: str = "2025-26"
    ) -> Dict[str, List[dict]]:
        """
        Fetch top 10 players for all tracked stats using parallel API calls.

        Returns:
            Dict mapping stat name to list of player dicts with rank info
        """
        rankings = {}

        # Use ThreadPoolExecutor for parallel API calls
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self._fetch_player_stat, stat, season_year): stat
                for stat in self.player_stats
            }
            for future in as_completed(futures):
                stat, players = future.result()
                rankings[stat] = players

        # Build index for O(1) lookups by team
        self._build_player_rankings_by_team(rankings)

        return rankings

    def _build_team_rankings_index(self, team_rankings: Dict[str, List[dict]]):
        """Build O(1) lookup index: team_id -> {stat: rank_info}"""
        self._team_rankings_index = {}
        for stat, teams in team_rankings.items():
            for team in teams:
                team_id = str(team["teamId"])
                if team_id not in self._team_rankings_index:
                    self._team_rankings_index[team_id] = {}
                self._team_rankings_index[team_id][stat] = {
                    "stat": self.TEAM_STAT_NAMES.get(stat, stat),
                    "rank": team["rank"],
                    "value": team["value"],
                }

    def _build_player_rankings_by_team(self, player_rankings: Dict[str, List[dict]]):
        """Build O(1) lookup index: team_tricode -> [player_rank_info, ...]"""
        self._player_rankings_by_team = {}
        for stat, players in player_rankings.items():
            for player in players:
                if player["rank"] <= 10:
                    tricode = player["teamTricode"]
                    if tricode not in self._player_rankings_by_team:
                        self._player_rankings_by_team[tricode] = []
                    self._player_rankings_by_team[tricode].append(
                        {
                            "playerName": player["playerName"],
                            "stat": self.PLAYER_STAT_NAMES.get(stat, stat),
                            "rank": player["rank"],
                            "value": player["value"],
                        }
                    )

    def get_team_rankings(
        self, team_id: str, team_rankings: Dict[str, List[dict]]
    ) -> List[dict]:
        """
        Get all rankings for a specific team using O(1) index lookup.

        Returns:
            List of dicts with stat, rank, and value
        """
        # Use index if available (O(1) lookup)
        if self._team_rankings_index is not None:
            team_data = self._team_rankings_index.get(str(team_id), {})
            team_ranks = list(team_data.values())
            return sorted(team_ranks, key=lambda x: x["rank"])

        # Fallback to iteration if index not built
        team_ranks = []
        for stat, teams in team_rankings.items():
            for team in teams:
                if str(team["teamId"]) == str(team_id):
                    team_ranks.append(
                        {
                            "stat": self.TEAM_STAT_NAMES.get(stat, stat),
                            "rank": team["rank"],
                            "value": team["value"],
                        }
                    )
                    break
        return sorted(team_ranks, key=lambda x: x["rank"])

    def get_player_rankings_for_team(
        self, team_tricode: str, player_rankings: Dict[str, List[dict]]
    ) -> List[dict]:
        """
        Get all top-10 players from a specific team using O(1) index lookup.

        Returns:
            List of dicts with player name, stat, rank, and value
        """
        # Use index if available (O(1) lookup)
        if self._player_rankings_by_team is not None:
            player_ranks = self._player_rankings_by_team.get(team_tricode, [])
            return sorted(player_ranks, key=lambda x: (x["rank"], x["playerName"]))

        # Fallback to iteration if index not built
        player_ranks = []
        for stat, players in player_rankings.items():
            for player in players:
                if player["teamTricode"] == team_tricode and player["rank"] <= 10:
                    player_ranks.append(
                        {
                            "playerName": player["playerName"],
                            "stat": self.PLAYER_STAT_NAMES.get(stat, stat),
                            "rank": player["rank"],
                            "value": player["value"],
                        }
                    )
        return sorted(player_ranks, key=lambda x: (x["rank"], x["playerName"]))
