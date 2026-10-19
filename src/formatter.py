from datetime import date, datetime

from . import injuries as inj
from .mapping import get_broadcaster_emoji


def format_time(game_time_est: str) -> str:
    try:
        dt = datetime.fromisoformat(game_time_est.replace("Z", "+00:00"))
        return dt.strftime("%I:%M %p ET").lstrip("0")
    except Exception:
        return "TBD"


def format_clinch_indicator(clinch_indicator: str) -> str:
    """Normalize the standings clinch indicator for the game header, e.g. "x" -> " - x"."""
    normalized = str(clinch_indicator or "").strip()
    if not normalized:
        return ""
    return f" {normalized}" if normalized.startswith("-") else f" - {normalized}"


def national_tv(game: dict) -> list:
    """Every national TV broadcaster for a game, in API order, deduplicated."""
    names = []
    for broadcasters in (game.get("broadcasters") or {}).values():
        for b in broadcasters or []:
            if b.get("broadcasterScope") == "natl" and b.get("broadcasterMedia") == "tv":
                name = b.get("broadcasterDisplay", "")
                if name and name not in names:
                    names.append(name)
    return names


def games_on(schedule: dict, day: date) -> list:
    """Games on a date, sorted by start time with nationally televised games first."""
    target = day.strftime("%m/%d/%Y")
    for game_date in schedule.get("leagueSchedule", {}).get("gameDates", []):
        if game_date.get("gameDate", "").startswith(target):
            games = game_date.get("games", [])
            break
    else:
        return []

    def sort_key(game):
        try:
            dt = datetime.fromisoformat(game.get("gameTimeEst", "").replace("Z", "+00:00"))
        except ValueError:
            dt = datetime.max
        return (dt, 0 if national_tv(game) else 1)

    return sorted(games, key=sort_key)


def index_standings(data: dict) -> dict:
    return {t.get("teamId"): t for t in data.get("leagueStandings", {}).get("teams", [])}


class GameFormatter:
    """Builds the parent message, standings/rankings reply and injury reply for each game."""

    PARENT_TEAM_STATS = {"PPG", "FG%", "3P%", "BLK", "Opp PPG", "3PM"}
    THREAD_TEAM_STATS = {"Net RTG", "Off RTG", "Def RTG", "AST", "REB", "STL"}
    PERCENT_STATS = {"FG%", "3P%"}

    def __init__(self, rankings, standings: dict, injuries: dict = None, milestones=None):
        self.rankings = rankings
        self.standings = standings
        self.injuries = injuries  # None when the channel doesn't show injuries
        self.milestones = milestones  # None when the channel doesn't show milestones

    def format_game(self, game: dict) -> dict:
        away, home = game.get("awayTeam", {}), game.get("homeTeam", {})
        away_id, home_id = away.get("teamId"), home.get("teamId")
        away_tri, home_tri = away.get("teamTricode", ""), home.get("teamTricode", "")
        teams = ((away_id, away_tri), (home_id, home_tri))

        thread_rankings = [
            *(self._team_line(tid, tri, self.THREAD_TEAM_STATS) for tid, tri in teams),
            *(self._player_lines(tri, 6, 10) for _, tri in teams),
        ]
        thread_rankings = [line for line in thread_rankings if line]

        parent = [
            self._header(game),
            *(self._streak_line(tid, tri) for tid, tri in teams),
            *(self._team_line(tid, tri, self.PARENT_TEAM_STATS) for tid, tri in teams),
            *(self._player_lines(tri, 1, 5) for _, tri in teams),
            ":t10: Other Top 10s threaded" if thread_rankings else "",
            ":notable: NOTABLES",
        ]
        # Mookie fills these sections; other channels (and games with nothing to report)
        # keep the placeholder line so every channel shares one layout.
        milestones = self.milestones.milestones_for_teams(away_id, home_id) if self.milestones else []
        parent += [f":mst: {line}" for line in milestones] or [":mst: MILESTONES"]
        injury_summary = inj.format_summary(self.injuries, away_id, home_id) if self.injuries is not None else ""
        parent.append(injury_summary or ":out: INJURIES")

        injury_thread = None
        if self.injuries is not None:
            injury_thread = inj.format_thread(self.injuries, away_id, home_id, away_tri, home_tri) or None

        # Always posted: home/away records lead, then the thread rankings.
        thread_lines = [
            self._location_line(away_id, away_tri, home=False),
            self._location_line(home_id, home_tri, home=True),
            *thread_rankings,
        ]
        thread = "\n".join(line for line in thread_lines if line) or None

        return {
            "parent": "\n".join(line for line in parent if line),
            "thread": thread,
            "injury_thread": injury_thread,
        }

    def _header(self, game: dict) -> str:
        away, home = (self._side(game.get(key, {})) for key in ("awayTeam", "homeTeam"))
        away_logo = f":_{game.get('awayTeam', {}).get('teamTricode', '').lower()}:"
        home_logo = f":_{game.get('homeTeam', {}).get('teamTricode', '').lower()}:"
        # Logos sit on the outside of "at": `#8 MIN (0-0) :_min: at :_mia: #9 MIA (0-0)`.
        header = f"{away} {away_logo} at {home_logo} {home} | {format_time(game.get('gameTimeEst', ''))}"
        # Dedupe on the emoji: NBC and Telemundo share :_nbc_peacock:.
        tv = " ".join(dict.fromkeys(get_broadcaster_emoji(name) for name in national_tv(game)))
        return f"{header} | {tv}" if tv else header

    def _side(self, team: dict) -> str:
        """`#seed TRI (W-L)` plus the clinch indicator, e.g. `#1 OKC (56-15) - w`."""
        standing = self.standings.get(team.get("teamId"), {})
        rank = standing.get("playoffRank")
        seed = f"#{rank} " if rank else ""
        clinch = format_clinch_indicator(standing.get("clinchIndicator"))
        return f"{seed}{team.get('teamTricode', '')} ({team.get('wins', 0)}-{team.get('losses', 0)}){clinch}"

    def _streak_line(self, team_id, tri: str) -> str:
        standing = self.standings.get(team_id)
        if not standing:
            return ""
        return f":_{tri.lower()}: {standing.get('currentStreakText', '')} | L10: {standing.get('l10', '')}"

    def _location_line(self, team_id, tri: str, home: bool) -> str:
        standing = self.standings.get(team_id)
        if not standing:
            return ""
        if home:
            return f":_{tri.lower()}: Home: {standing.get('home', '')} | L10: {standing.get('l10Home', '')}"
        return f":_{tri.lower()}: Away: {standing.get('road', '')} | L10: {standing.get('l10Road', '')}"

    def _team_line(self, team_id, tri: str, stats: set) -> str:
        parts = [
            f"#{r['rank']} in {r['stat']} ({r['value']:.1f})"
            for r in self.rankings.team_rankings(team_id)
            if r["stat"] in stats
        ]
        return f":t10: {tri} ranks {', '.join(parts)}" if parts else ""

    def _player_lines(self, tri: str, min_rank: int, max_rank: int) -> str:
        """One line per player (alphabetical) with their ranks in [min_rank, max_rank]."""
        order = self.rankings.PLAYER_STAT_ORDER
        by_player = {}
        for r in self.rankings.player_rankings(tri):
            if min_rank <= r["rank"] <= max_rank:
                by_player.setdefault(r["playerName"], []).append(r)
        lines = []
        for name in sorted(by_player):
            parts = []
            for r in sorted(by_player[name], key=lambda r: order.index(r["stat"])):
                value = r["value"] * 100 if r["stat"] in self.PERCENT_STATS else r["value"]
                parts.append(f"#{r['rank']} in {r['stat']} ({value:.1f})")
            lines.append(f":t10: {name} ({tri}) ranks {', '.join(parts)}")
        return "\n".join(lines)
