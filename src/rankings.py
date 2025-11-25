# src/rankings.py
from typing import Dict, List, Set, Tuple
from .nba_api import NBAClient


class RankingsChecker:
    """Handles fetching and checking NBA rankings for teams and players"""

    # Friendly names for stats
    TEAM_STAT_NAMES = {
        "BASE_PTS": "PPG",
        "BASE_FG_PCT": "FG%",
        "BASE_FG3_PCT": "3P%",
        "BASE_AST": "AST",
        "BASE_REB": "REB",
    }

    # Mapping from request stat to API response stat key
    TEAM_STAT_RESPONSE_KEYS = {
        "BASE_PTS": "PTS_PG",
        "BASE_FG_PCT": "FG_PCT",
        "BASE_FG3_PCT": "FG3_PCT",
        "BASE_AST": "AST_PG",
        "BASE_REB": "REB_PG",
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

    def get_all_top_teams(self, season_year: str = "2025-26") -> Dict[str, List[dict]]:
        """
        Fetch top 10 teams for all tracked stats.

        Returns:
            Dict mapping stat name to list of team dicts with rank info
        """
        rankings = {}

        for stat in self.team_stats:
            try:
                response = self.client.get_top_teams_by_stat(
                    stat, limit=10, season_year=season_year
                )

                # DEBUG: Print response structure
                # print(f"\n=== DEBUG: {stat} response ===")
                # print(f"Keys in response: {response.keys()}")

                # Changed from 'results' to 'teams'
                teams_data = response.get("teams", [])

                # if len(teams_data) > 0:
                # print(f"First team: {teams_data[0]}")

                # Store full results with rank
                teams = []
                # Get the correct response key for this stat
                response_stat_key = self.TEAM_STAT_RESPONSE_KEYS.get(stat, stat)

                for rank, team in enumerate(teams_data, start=1):
                    teams.append(
                        {
                            "teamId": str(
                                team.get("teamId")
                            ),  # Convert to string for consistency
                            "teamName": team.get("teamName", ""),
                            "teamTricode": team.get("teamTricode", ""),
                            "rank": rank,
                            "value": team.get("stats", {}).get(response_stat_key, 0),
                        }
                    )
                rankings[stat] = teams
                # print(f"Stored {len(teams)} teams for {stat}")

            except Exception as e:
                # print(f"Warning: Failed to fetch top teams for {stat}: {e}")
                rankings[stat] = []

        return rankings

    def get_all_top_players(
        self, season_year: str = "2025-26"
    ) -> Dict[str, List[dict]]:
        """
        Fetch top 10 players for all tracked stats.

        Each stat category is fetched separately from the API to ensure
        accurate rankings (not sorted locally).

        Returns:
            Dict mapping stat name to list of player dicts with rank info
        """
        rankings = {}

        # Fetch top players for each stat category separately
        for stat in self.player_stats:
            try:
                # Get the API stat category for this stat
                api_stat_category = self.PLAYER_STAT_API_CATEGORIES.get(stat, stat)

                response = self.client.get_top_players_by_stat(
                    api_stat_category,
                    limit=10,
                    season_year=season_year,
                )

                players_data = response.get("players", [])

                # Get the response key for extracting the stat value
                stat_key = self.PLAYER_STAT_RESPONSE_KEYS.get(stat, stat.lower())

                # Store with proper structure (limit to top 10)
                players = []
                for player in players_data[:10]:
                    players.append(
                        {
                            "playerId": str(
                                player.get("personId", "")
                            ),  # API uses 'personId'
                            "playerName": player.get("name", ""),  # API uses 'name'
                            "teamTricode": player.get(
                                "teamAbbreviation", ""
                            ),  # API uses 'teamAbbreviation'
                            "rank": player.get("rank", 0),  # Use API's official rank
                            "value": player.get(stat_key, 0),
                        }
                    )
                rankings[stat] = players

            except Exception as e:
                # print(f"Warning: Failed to fetch player data for {stat}: {e}")
                rankings[stat] = []

        return rankings

    def get_team_rankings(
        self, team_id: str, team_rankings: Dict[str, List[dict]]
    ) -> List[dict]:
        """
        Get all rankings for a specific team.

        Returns:
            List of dicts with stat, rank, and value
        """
        team_ranks = []

        # DEBUG: Print what we're looking for
        # print(
        #    f"\n=== DEBUG: Looking for team_id: {team_id} (type: {type(team_id)}) ==="
        # )

        for stat, teams in team_rankings.items():
            # print(f"Checking {stat} - {len(teams)} teams")
            for team in teams:
                # print(
                #    f"  Team ID: {team['teamId']} (type: {type(team['teamId'])}) - {team.get('teamTricode')}"
                # )
                if str(team["teamId"]) == str(team_id):  # Force string comparison
                    # print(f"  ✓ MATCH FOUND!")
                    team_ranks.append(
                        {
                            "stat": self.TEAM_STAT_NAMES.get(stat, stat),
                            "rank": team["rank"],
                            "value": team["value"],
                        }
                    )
                    break

        # print(f"Found {len(team_ranks)} rankings for team {team_id}")
        return sorted(team_ranks, key=lambda x: x["rank"])

    def get_player_rankings_for_team(
        self, team_tricode: str, player_rankings: Dict[str, List[dict]]
    ) -> List[dict]:
        """
        Get all top-10 players from a specific team.

        Returns:
            List of dicts with player name, stat, rank, and value
            Example: [{"playerName": "Trae Young", "stat": "PPG", "rank": 2, "value": 28.5}, ...]
        """
        player_ranks = []

        for stat, players in player_rankings.items():
            for player in players:
                # Only include players in the top 10 for this stat
                if player["teamTricode"] == team_tricode and player["rank"] <= 10:
                    player_ranks.append(
                        {
                            "playerName": player["playerName"],
                            "stat": self.PLAYER_STAT_NAMES.get(stat, stat),
                            "rank": player["rank"],
                            "value": player["value"],
                        }
                    )

        # Sort by rank, then by player name for consistency
        return sorted(player_ranks, key=lambda x: (x["rank"], x["playerName"]))
