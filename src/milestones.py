from concurrent.futures import ThreadPoolExecutor

from .nba_api import NBAClient


def ordinal(n: int) -> str:
    suffix = "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


class MilestonesChecker:
    """
    Reports active players within a gap threshold of passing the player directly
    above them on an all-time regular-season career leaderboard.

        Brook Lopez (1,945) needs 6 BLK to pass Dikembe Mutombo (1,950) for 19th
    """

    # measure -> (display label, sort column, gap threshold in career totals).
    # Thresholds were tuned for the WNBA; adjust for the NBA as needed.
    STATS = {
        "BASE_PTS": ("PTS", "PTS", 50),
        "BASE_REB": ("REB", "REB", 15),
        "BASE_AST": ("AST", "AST", 15),
        "BASE_FGM": ("FGM", "FGM", 15),
        "BASE_FTM": ("FTM", "FTM", 10),
        "BASE_STL": ("STL", "STL", 10),
        "BASE_BLK": ("BLK", "BLK", 10),
        "BASE_FG3M": ("3PM", "FG3M", 10),
    }

    MAX_ROWS = 250
    # Only report passing into this rank or better; a player is at most one spot below it.
    MAX_RANK = 20

    def __init__(self, client: NBAClient, season: str):
        self.client = client
        self.season = season
        # measure -> [{rank, playerId, name, value}] in rank order
        self._leaderboards = {}
        # team_id -> {playerId}
        self._rosters = {}

    def _fetch_leaderboard(self, measure: str) -> list:
        label, sort_col, _ = self.STATS[measure]
        try:
            players = self.client.get_career_leaders(measure, sort_col, self.MAX_ROWS)
        except Exception as e:
            print(f"Warning: could not fetch career {label}: {e}")
            return []
        return [
            {
                "rank": rank,
                "playerId": p.get("playerId"),
                "name": p.get("name", ""),
                "value": p.get("stats", {}).get(sort_col, 0),
            }
            for rank, p in enumerate(players, start=1)
        ]

    def _fetch_roster(self, team_id) -> set:
        try:
            roster = self.client.get_team_roster(team_id, self.season)
        except Exception as e:
            print(f"Warning: could not fetch roster for team {team_id}: {e}")
            return set()
        return {p["playerId"] for p in roster if p.get("playerId") is not None}

    def load(self, team_ids):
        """Fetch every career leaderboard and each team's roster once, in parallel."""
        team_ids = list(dict.fromkeys(team_ids))
        with ThreadPoolExecutor(max_workers=10) as executor:
            boards = {m: executor.submit(self._fetch_leaderboard, m) for m in self.STATS}
            rosters = {t: executor.submit(self._fetch_roster, t) for t in team_ids}
            self._leaderboards = {m: f.result() for m, f in boards.items()}
            self._rosters = {t: f.result() for t, f in rosters.items()}

    def milestones_for_teams(self, *team_ids) -> list:
        player_ids = set().union(*(self._rosters.get(t, set()) for t in team_ids))
        lines = []
        for measure, (label, _, threshold) in self.STATS.items():
            rows = self._leaderboards.get(measure, [])
            for i, row in enumerate(rows[1 : self.MAX_RANK + 1], start=1):
                if row["playerId"] not in player_ids:
                    continue
                above = rows[i - 1]
                # +1: matching the value only ties; one more is needed to pass.
                needed = above["value"] - row["value"] + 1
                if needed <= 0 or needed > threshold:
                    continue
                lines.append(
                    f"{row['name']} ({row['value']:,.0f}) needs {needed:,.0f} {label} "
                    f"to pass {above['name']} ({above['value']:,.0f}) for {ordinal(above['rank'])}"
                )
        return lines
