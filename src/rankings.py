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
    }

    # Map stat names to their API response keys (lowercase)
    PLAYER_STAT_RESPONSE_KEYS = {
        "PTS": "pts",
        "AST": "ast",
        "REB": "reb",
        "STL": "stl",
        "BLK": "blk",
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

        Note: The API only returns data for PTS stat category, so we fetch that
        and then sort by each stat locally to create separate rankings.

        Returns:
            Dict mapping stat name to list of player dicts with rank info
        """
        rankings = {}

        # Fetch all players sorted by PTS (this returns ~277 players with all stats)
        try:
            response = self.client.get_top_players_by_stat(
                "PTS",
                limit=300,
                season_year=season_year,  # Get more players to ensure top 10 for other stats
            )

            # DEBUG: Print response structure
            # print("\n=== DEBUG: Fetching all players with PTS to extract other stats ===")
            # print(f"Keys in response: {response.keys()}")

            players_data = response.get("players", [])
            # print(f"Retrieved {len(players_data)} players")

            # if len(players_data) > 0:
            #    print(f"First player sample: {players_data[0]}")

            # Create rankings for each stat by sorting the players
            for stat in self.player_stats:
                stat_key = self.PLAYER_STAT_RESPONSE_KEYS.get(stat, stat.lower())

                # Sort players by this stat (descending)
                sorted_players = sorted(
                    players_data, key=lambda p: p.get(stat_key, 0), reverse=True
                )[:10]  # Take top 10

                # Store with proper structure
                players = []
                for rank, player in enumerate(sorted_players, start=1):
                    players.append(
                        {
                            "playerId": str(
                                player.get("personId", "")
                            ),  # API uses 'personId'
                            "playerName": player.get("name", ""),  # API uses 'name'
                            "teamTricode": player.get(
                                "teamAbbreviation", ""
                            ),  # API uses 'teamAbbreviation'
                            "rank": rank,
                            "value": player.get(stat_key, 0),
                        }
                    )
                rankings[stat] = players
                # print(f"Stored top 10 players for {stat}")

        except Exception as e:
            # print(f"Warning: Failed to fetch player data: {e}")
            # Initialize empty rankings for all stats
            for stat in self.player_stats:
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
                if player["teamTricode"] == team_tricode:
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
