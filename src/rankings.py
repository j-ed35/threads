from concurrent.futures import ThreadPoolExecutor

from .nba_api import NBAClient


class RankingsChecker:
    """Fetches season top-10 team and player rankings and indexes them for O(1) lookups."""

    # measure -> (response stat key / sort column, display label, lower-is-better)
    TEAM_STATS = {
        "BASE_PTS": ("PTS_PG", "PPG", False),
        "BASE_FG_PCT": ("FG_PCT", "FG%", False),
        "BASE_FG3_PCT": ("FG3_PCT", "3P%", False),
        "BASE_FG3M": ("FG3M_PG", "3PM", False),
        "BASE_AST": ("AST_PG", "AST", False),
        "BASE_REB": ("REB_PG", "REB", False),
        "BASE_STL": ("STL_PG", "STL", False),
        "BASE_BLK": ("BLK_PG", "BLK", False),
        "OPP_PTS": ("OPP_PTS_PG", "Opp PPG", True),
        "ADV_TM_NET_RATING": ("TM_NET_RATING", "Net RTG", False),
        "ADV_TM_OFF_RATING": ("TM_OFF_RATING", "Off RTG", False),
        "ADV_TM_DEF_RATING": ("TM_DEF_RATING", "Def RTG", True),
    }

    # leaders statCategory -> (response key, display label). Order is the display order.
    PLAYER_STATS = {
        "PTS": ("pts", "PPG"),
        "REB": ("reb", "RPG"),
        "AST": ("ast", "APG"),
        "FG_PCT": ("fgPct", "FG%"),
        "FG3_PCT": ("fg3Pct", "3P%"),
        "FG3M": ("fg3m", "3PM"),
        "STL": ("stl", "SPG"),
        "BLK": ("blk", "BPG"),
    }
    PLAYER_STAT_ORDER = [label for _, label in PLAYER_STATS.values()]
    TEAM_STAT_ORDER = [label for _, label, _ in TEAM_STATS.values()]

    def __init__(self, client: NBAClient):
        self.client = client
        # team_id -> [{stat, rank, value}]
        self._teams = {}
        # team tricode -> [{playerName, stat, rank, value}]
        self._players = {}

    def _fetch_team_stat(self, measure: str, season: str) -> list:
        sort_col, label, ascending = self.TEAM_STATS[measure]
        try:
            teams = self.client.get_top_teams(measure, sort_col, ascending, season)
        except Exception as e:
            print(f"Warning: could not fetch team {label}: {e}")
            teams = []
        return [
            (str(t.get("teamId")), {"stat": label, "rank": rank, "value": t.get("stats", {}).get(sort_col, 0)})
            for rank, t in enumerate(teams, start=1)
        ]

    def _fetch_player_stat(self, category: str, season: str) -> list:
        key, label = self.PLAYER_STATS[category]
        try:
            players = self.client.get_top_players(category, season)
        except Exception as e:
            print(f"Warning: could not fetch player {label}: {e}")
            players = []
        return [
            (
                p.get("teamAbbreviation", ""),
                {"playerName": p.get("name", ""), "stat": label, "rank": p.get("rank", 0), "value": p.get(key, 0)},
            )
            for p in players
            if 0 < p.get("rank", 0) <= 10
        ]

    def load(self, season: str):
        """Fetch every team and player stat in parallel and build the indexes."""
        with ThreadPoolExecutor(max_workers=10) as executor:
            team_futures = [executor.submit(self._fetch_team_stat, m, season) for m in self.TEAM_STATS]
            player_futures = [executor.submit(self._fetch_player_stat, c, season) for c in self.PLAYER_STATS]
            for future in team_futures:
                for team_id, info in future.result():
                    self._teams.setdefault(team_id, []).append(info)
            for future in player_futures:
                for tricode, info in future.result():
                    self._players.setdefault(tricode, []).append(info)

    def team_rankings(self, team_id) -> list:
        """A team's top-10 ranks, ordered by rank then display order."""
        ranks = self._teams.get(str(team_id), [])
        return sorted(ranks, key=lambda r: (r["rank"], self.TEAM_STAT_ORDER.index(r["stat"])))

    def player_rankings(self, tricode: str) -> list:
        """Every top-10 rank held by a player on this team."""
        return self._players.get(tricode, [])
