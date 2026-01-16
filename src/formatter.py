from datetime import datetime
from .broadcaster_mapping import get_broadcaster_emoji


class GameFormatter:
    """Format NBA game data for Slack messages with parent/thread structure."""

    # Class-level cache for standings data (shared across instances)
    _standings_cache = None

    # Stats to show in parent message (limited set)
    PARENT_TEAM_STATS = {"PPG", "FG%", "3P%", "BLK", "Opp PPG", "3PM"}
    PARENT_PLAYER_STATS = {"PPG", "APG", "RPG", "FG%", "3PM", "3P%"}

    # Stats to show in thread message (advanced/remaining)
    THREAD_TEAM_STATS = {"Net RTG", "Off RTG", "Def RTG", "AST", "REB", "STL"}
    THREAD_PLAYER_STATS = {"SPG", "BPG", "Double Doubles", "Triple Doubles"}

    def __init__(self, nba_client, rankings_checker=None):
        """
        Initialize formatter with NBA client and optional rankings checker.

        Args:
            nba_client: Instance of NBAClient for API calls
            rankings_checker: Instance of RankingsChecker for rankings data
        """
        self.nba_client = nba_client
        self.rankings_checker = rankings_checker
        self.team_rankings = None
        self.player_rankings = None

    @classmethod
    def clear_standings_cache(cls):
        """Clear the standings cache (useful for testing or forcing refresh)."""
        cls._standings_cache = None

    def load_rankings(self, season_year: str = "2025-26"):
        """
        Fetch and cache rankings data for the day.

        Args:
            season_year: Season year (e.g., "2025-26")
        """
        if self.rankings_checker:
            print("Fetching team and player rankings...")
            self.team_rankings = self.rankings_checker.get_all_top_teams(season_year)
            self.player_rankings = self.rankings_checker.get_all_top_players(
                season_year
            )
            print(
                f"Rankings loaded: {len(self.team_rankings)} team stats, {len(self.player_rankings)} player stats"
            )

    @staticmethod
    def format_time(game_time_est):
        """Convert ISO time to readable format."""
        try:
            dt = datetime.fromisoformat(game_time_est.replace("Z", "+00:00"))
            return dt.strftime("%I:%M %p ET").lstrip("0")
        except Exception:
            return "TBD"

    def format_games_with_threads(self, data: dict) -> list:
        """
        Format game data into parent/thread message pairs.

        Args:
            data: Schedule data from NBA API

        Returns:
            List of dicts with 'parent' and 'thread' message texts
        """
        standings_lookup = self._create_standings_lookup()
        games = self._extract_games(data)

        if not games:
            return []

        formatted_games = []
        for game in games:
            parent_text, thread_text = self._format_game_with_thread(
                game, standings_lookup
            )
            formatted_games.append({
                "parent": parent_text,
                "thread": thread_text,
            })

        return formatted_games

    def format_games(self, data: dict) -> str:
        """
        Format game data (legacy single-message format).

        Args:
            data: Schedule data from NBA API

        Returns:
            Formatted string for Slack message
        """
        standings_lookup = self._create_standings_lookup()
        games = self._extract_games(data)

        if not games:
            return "No games scheduled"

        formatted_games = []
        for game in games:
            parent_text, _ = self._format_game_with_thread(game, standings_lookup)
            formatted_games.append(parent_text)

        return "\n".join(formatted_games)

    def _extract_games(self, data: dict) -> list:
        """Extract games list from API response."""
        if not data or "leagueSchedule" not in data:
            return []

        league_schedule = data["leagueSchedule"]
        if not league_schedule or "gameDates" not in league_schedule:
            return []

        game_dates = league_schedule["gameDates"]
        today_str = datetime.now().strftime("%m/%d/%Y")

        for game_date in game_dates:
            date_str = game_date.get("gameDate", "")
            if today_str in date_str:
                return game_date.get("games", [])

        return []

    def _create_standings_lookup(self) -> dict:
        """
        Create a lookup dictionary for team standings data.
        Uses class-level cache to avoid redundant API calls.

        Returns:
            Dictionary mapping teamId to standings data
        """
        if GameFormatter._standings_cache is not None:
            return GameFormatter._standings_cache

        try:
            standings_data = self.nba_client.get_team_standings()
            lookup = {}

            teams = standings_data.get("leagueStandings", {}).get("teams", [])
            current_month = datetime.now().strftime("%b").lower()

            for team in teams:
                team_id = team.get("teamId")
                lookup[team_id] = {
                    "playoffRank": team.get("playoffRank", ""),
                    "currentStreakText": team.get("currentStreakText", ""),
                    "l10": team.get("l10", ""),
                    "home": team.get("home", ""),
                    "road": team.get("road", ""),
                    "l10Home": team.get("l10Home", ""),
                    "l10Road": team.get("l10Road", ""),
                    "month": team.get(current_month, ""),
                }

            GameFormatter._standings_cache = lookup
            return lookup

        except Exception as e:
            print(f"Warning: Could not fetch standings data: {e}")
            return {}

    def _format_game_with_thread(
        self, game: dict, standings_lookup: dict
    ) -> tuple:
        """
        Format a single game into parent and thread messages.

        Args:
            game: Game data dictionary
            standings_lookup: Standings lookup dictionary

        Returns:
            Tuple of (parent_text, thread_text)
        """
        away_team = game.get("awayTeam", {})
        home_team = game.get("homeTeam", {})

        away_tricode = away_team.get("teamTricode", "")
        home_tricode = home_team.get("teamTricode", "")
        away_wins = away_team.get("wins", 0)
        away_losses = away_team.get("losses", 0)
        home_wins = home_team.get("wins", 0)
        home_losses = home_team.get("losses", 0)

        away_team_id = away_team.get("teamId")
        home_team_id = home_team.get("teamId")
        away_rank = standings_lookup.get(away_team_id, {}).get("playoffRank", "")
        home_rank = standings_lookup.get(home_team_id, {}).get("playoffRank", "")

        game_time = self.format_time(game.get("gameTimeEst", ""))

        # Broadcaster
        broadcasters = game.get("broadcasters", {})
        national_broadcasters = broadcasters.get("nationalBroadcasters", [])
        broadcaster_text = ""
        if national_broadcasters and len(national_broadcasters) > 0:
            broadcaster_display = national_broadcasters[0].get("broadcasterDisplay", "")
            if broadcaster_display:
                broadcaster_text = f" | {get_broadcaster_emoji(broadcaster_display)}"

        # === PARENT MESSAGE ===
        parent_lines = []

        # Game header with playoff ranks
        parent_lines.append(
            f"#{away_rank} {away_tricode} ({away_wins}-{away_losses}) :_{away_tricode.lower()}: at "
            f"#{home_rank} {home_tricode} ({home_wins}-{home_losses}) :_{home_tricode.lower()}: | {game_time}{broadcaster_text}"
        )

        # Standings lines (streak + L10 only in parent)
        parent_lines.append(self._format_parent_standings(
            away_team_id, away_tricode, standings_lookup
        ))
        parent_lines.append(self._format_parent_standings(
            home_team_id, home_tricode, standings_lookup
        ))

        # Team rankings (parent stats only)
        parent_lines.append(self._format_team_rankings_filtered(
            away_team_id, away_tricode, self.PARENT_TEAM_STATS
        ))
        parent_lines.append(self._format_team_rankings_filtered(
            home_team_id, home_tricode, self.PARENT_TEAM_STATS
        ))

        # Player rankings (parent stats only)
        parent_lines.append(self._format_player_rankings_filtered(
            away_tricode, self.PARENT_PLAYER_STATS
        ))
        parent_lines.append(self._format_player_rankings_filtered(
            home_tricode, self.PARENT_PLAYER_STATS
        ))

        # Check if there are thread stats to show
        has_thread_stats = self._has_thread_stats(
            away_team_id, home_team_id, away_tricode, home_tricode
        )
        if has_thread_stats:
            parent_lines.append(":t10: Other Top 10s threaded")

        # Footer sections
        parent_lines.append(":notable: NOTABLES")
        parent_lines.append(":mst: MILESTONES")
        parent_lines.append(":gtd: GTD/QUESTIONABLE")
        parent_lines.append(":out: INJURIES")

        parent_text = "\n".join(line for line in parent_lines if line)

        # === THREAD MESSAGE ===
        thread_lines = []

        # Thread header
        thread_lines.append(f":_{away_tricode.lower()}: @ :_{home_tricode.lower()}:")

        # Home/Away records with L10
        thread_lines.append(self._format_thread_standings(
            away_team_id, away_tricode, standings_lookup, is_home=False
        ))
        thread_lines.append(self._format_thread_standings(
            home_team_id, home_tricode, standings_lookup, is_home=True
        ))

        # Team rankings (thread/advanced stats only)
        thread_lines.append(self._format_team_rankings_filtered(
            away_team_id, away_tricode, self.THREAD_TEAM_STATS
        ))
        thread_lines.append(self._format_team_rankings_filtered(
            home_team_id, home_tricode, self.THREAD_TEAM_STATS
        ))

        # Player rankings (thread stats only)
        thread_lines.append(self._format_player_rankings_filtered(
            away_tricode, self.THREAD_PLAYER_STATS
        ))
        thread_lines.append(self._format_player_rankings_filtered(
            home_tricode, self.THREAD_PLAYER_STATS
        ))

        thread_text = "\n".join(line for line in thread_lines if line)

        # Only return thread text if there's meaningful content
        thread_content = thread_text.strip()
        has_content = any(
            line.strip() and not line.startswith(":_")
            for line in thread_lines[3:]  # Skip header and standings lines
        )

        return parent_text, thread_text if has_content else None

    def _format_parent_standings(
        self, team_id: int, team_tricode: str, standings_lookup: dict
    ) -> str:
        """Format standings line for parent message (streak + L10)."""
        if team_id not in standings_lookup:
            return ""

        team_data = standings_lookup[team_id]
        streak = team_data.get("currentStreakText", "")
        l10 = team_data.get("l10", "")

        return f":_{team_tricode.lower()}: {streak} | L10: {l10}"

    def _format_thread_standings(
        self, team_id: int, team_tricode: str, standings_lookup: dict, is_home: bool
    ) -> str:
        """Format standings line for thread message (home/away record + L10)."""
        if team_id not in standings_lookup:
            return ""

        team_data = standings_lookup[team_id]

        if is_home:
            record = team_data.get("home", "")
            l10_record = team_data.get("l10Home", "")
            location = "Home"
        else:
            record = team_data.get("road", "")
            l10_record = team_data.get("l10Road", "")
            location = "Away"

        return f":_{team_tricode.lower()}: {location}: {record} | L10: {l10_record}"

    def _format_team_rankings_filtered(
        self, team_id: str, team_tricode: str, allowed_stats: set
    ) -> str:
        """
        Format team rankings lines for specified stats.

        Args:
            team_id: Team ID
            team_tricode: Team tricode (e.g., "ATL")
            allowed_stats: Set of stat names to include

        Returns:
            Formatted rankings string
        """
        if not self.rankings_checker or not self.team_rankings:
            return ""

        team_ranks = self.rankings_checker.get_team_rankings(
            str(team_id), self.team_rankings
        )

        if not team_ranks:
            return ""

        # Filter to allowed stats
        filtered_ranks = [r for r in team_ranks if r["stat"] in allowed_stats]

        if not filtered_ranks:
            return ""

        stat_parts = []
        for rank_info in filtered_ranks:
            stat_parts.append(
                f"#{rank_info['rank']} in {rank_info['stat']} ({rank_info['value']:.1f})"
            )

        stats_text = ", ".join(stat_parts)
        return f":t10: {team_tricode} ranks {stats_text}"

    # Stat groupings for player display formatting (in display order)
    PLAYER_STAT_GROUPS = [
        ["PPG", "RPG", "APG"],      # PTS, REB, AST
        ["FG%", "3P%", "3PM"],      # FG%, 3P%, 3PM
        ["SPG", "BPG"],             # STL, BLK
    ]

    def _format_player_rankings_filtered(
        self, team_tricode: str, allowed_stats: set
    ) -> str:
        """
        Format player rankings lines for specified stats, grouped by player.

        Args:
            team_tricode: Team tricode (e.g., "ATL")
            allowed_stats: Set of stat names to include

        Returns:
            Formatted player rankings string
        """
        if not self.rankings_checker or not self.player_rankings:
            return ""

        player_ranks = self.rankings_checker.get_player_rankings_for_team(
            team_tricode, self.player_rankings
        )

        if not player_ranks:
            return ""

        # Filter to allowed stats
        filtered_ranks = [r for r in player_ranks if r["stat"] in allowed_stats]

        if not filtered_ranks:
            return ""

        # Group by player
        player_stats = {}
        for rank_info in filtered_ranks:
            player_name = rank_info["playerName"]
            if player_name not in player_stats:
                player_stats[player_name] = {}
            player_stats[player_name][rank_info["stat"]] = rank_info

        # Stats that are totals (no decimal places)
        totals_stats = {"Double Doubles", "Triple Doubles"}

        lines = []
        for player_name in sorted(player_stats.keys()):
            stats = player_stats[player_name]

            # Build lines for each stat group
            for stat_group in self.PLAYER_STAT_GROUPS:
                group_parts = []
                for stat in stat_group:
                    if stat in stats:
                        rank_info = stats[stat]
                        value = rank_info["value"]

                        # Percentage stats need to be multiplied by 100
                        if stat in ["FG%", "3P%"]:
                            value = value * 100

                        # Format value based on stat type
                        if stat in totals_stats:
                            value_str = f"{value:.0f}"
                        else:
                            value_str = f"{value:.1f}"

                        group_parts.append(
                            f"#{rank_info['rank']} in {stat} ({value_str})"
                        )

                if group_parts:
                    stats_text = ", ".join(group_parts)
                    lines.append(
                        f":t10: {player_name} ({team_tricode}) ranks {stats_text}"
                    )

        return "\n".join(lines)

    def _has_thread_stats(
        self, away_team_id, home_team_id, away_tricode, home_tricode
    ) -> bool:
        """Check if there are any thread stats to display."""
        if not self.rankings_checker:
            return False

        # Check team thread stats
        for team_id in [away_team_id, home_team_id]:
            team_ranks = self.rankings_checker.get_team_rankings(
                str(team_id), self.team_rankings or {}
            )
            if any(r["stat"] in self.THREAD_TEAM_STATS for r in team_ranks):
                return True

        # Check player thread stats
        for tricode in [away_tricode, home_tricode]:
            player_ranks = self.rankings_checker.get_player_rankings_for_team(
                tricode, self.player_rankings or {}
            )
            if any(r["stat"] in self.THREAD_PLAYER_STATS for r in player_ranks):
                return True

        return False

    def _format_single_game(self, game: dict, standings_lookup: dict) -> str:
        """
        Format a single game (legacy method for compatibility).

        Args:
            game: Game data dictionary
            standings_lookup: Standings lookup dictionary

        Returns:
            Formatted game string (parent message only)
        """
        parent_text, _ = self._format_game_with_thread(game, standings_lookup)
        return parent_text
