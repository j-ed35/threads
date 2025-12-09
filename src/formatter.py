from datetime import datetime
from .broadcaster_mapping import get_broadcaster_emoji


class GameFormatter:
    """Format NBA game data for Slack messages."""

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
        except:
            return "TBD"

    def format_games(self, data: dict) -> str:
        """
        Format game data with standings, rankings, and pregame storylines.

        Args:
            data: Schedule data from NBA API

        Returns:
            Formatted string for Slack message
        """
        # Fetch standings once for all games
        standings_lookup = self._create_standings_lookup()

        games = self._extract_games(data)

        if not games:
            return "No games scheduled"

        formatted_games = []
        for game in games:
            game_text = self._format_single_game(game, standings_lookup)
            formatted_games.append(game_text)

        return "\n".join(formatted_games)

    def _extract_games(self, data: dict) -> list:
        """Extract games list from API response."""
        if not data or "leagueSchedule" not in data:
            return []

        league_schedule = data["leagueSchedule"]
        if not league_schedule or "gameDates" not in league_schedule:
            return []

        game_dates = league_schedule["gameDates"]

        # Get today's date in the format the API uses
        today_str = datetime.now().strftime("%m/%d/%Y")

        for game_date in game_dates:
            date_str = game_date.get("gameDate", "")
            if today_str in date_str:
                return game_date.get("games", [])

        return []

    def _create_standings_lookup(self) -> dict:
        """
        Create a lookup dictionary for team standings data.

        Returns:
            Dictionary mapping teamId to standings data
        """
        try:
            standings_data = self.nba_client.get_team_standings()
            lookup = {}

            teams = standings_data.get("leagueStandings", {}).get("teams", [])

            for team in teams:
                team_id = team.get("teamId")
                lookup[team_id] = {
                    "currentStreakText": team.get("currentStreakText", ""),
                    "l10": team.get("l10", ""),
                }

            return lookup

        except Exception as e:
            print(f"Warning: Could not fetch standings data: {e}")
            return {}

    def _format_team_standings_line(
        self, team_id: int, team_tricode: str, standings_lookup: dict
    ) -> str:
        """
        Format a single team's standings line.

        Args:
            team_id: Team ID
            team_tricode: Team tricode (e.g., "LAL")
            standings_lookup: Standings lookup dictionary

        Returns:
            Formatted standings line
        """
        if team_id not in standings_lookup:
            return ""

        team_data = standings_lookup[team_id]
        streak = team_data.get("currentStreakText", "")
        l10 = team_data.get("l10", "")

        return f":_{team_tricode.lower()}: {streak} | L10: {l10}\n"

    def _format_team_rankings(self, team_id: str, team_tricode: str) -> str:
        """
        Format team rankings lines, grouped by stat category.

        Args:
            team_id: Team ID
            team_tricode: Team tricode (e.g., "ATL")

        Returns:
            Formatted rankings string with stats grouped on separate lines
        """
        if not self.rankings_checker or not self.team_rankings:
            return ""

        team_ranks = self.rankings_checker.get_team_rankings(
            str(team_id), self.team_rankings
        )

        if not team_ranks:
            return ""

        # Get stat groups from RankingsChecker
        from .rankings import RankingsChecker
        stat_groups = RankingsChecker.TEAM_STAT_GROUPS

        # Create a mapping of friendly stat name to rank info
        stat_map = {rank_info['stat']: rank_info for rank_info in team_ranks}

        lines = []

        # Process each group (basic, advanced)
        for group_name, stat_keys in stat_groups.items():
            group_stats = []

            # Collect stats for this group that the team ranks in
            for stat_key in stat_keys:
                friendly_name = RankingsChecker.TEAM_STAT_NAMES.get(stat_key)
                if friendly_name and friendly_name in stat_map:
                    rank_info = stat_map[friendly_name]
                    group_stats.append(
                        f"#{rank_info['rank']} in {rank_info['stat']} ({rank_info['value']:.1f})"
                    )

            # If this team has any stats in this group, format them on one line
            if group_stats:
                stats_text = ", ".join(group_stats)
                lines.append(f":t10: {team_tricode} ranks {stats_text}\n")

        return "".join(lines)

    def _format_player_rankings(self, team_tricode: str) -> str:
        """
        Format player rankings lines for a team.

        Args:
            team_tricode: Team tricode (e.g., "ATL")

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

        # Group stats by player
        players_dict = {}
        for player_info in player_ranks:
            player_name = player_info["playerName"]
            if player_name not in players_dict:
                players_dict[player_name] = []

            # Percentage stats need to be multiplied by 100
            value = player_info["value"]
            if player_info["stat"] in ["FG%", "3P%"]:
                value = value * 100

            players_dict[player_name].append(
                {
                    "rank": player_info["rank"],
                    "stat": player_info["stat"],
                    "value": value,
                }
            )

        # Format one line per player with all their stats
        lines = []
        for player_name, stats in players_dict.items():
            stat_parts = []
            for stat_info in stats:
                stat_parts.append(
                    f"#{stat_info['rank']} in {stat_info['stat']} ({stat_info['value']:.1f})"
                )

            stats_text = ", ".join(stat_parts)
            lines.append(f":t10: {player_name} ({team_tricode}) ranks {stats_text}\n")

        return "".join(lines)

    def _format_single_game(self, game: dict, standings_lookup: dict) -> str:
        """
        Format a single game with standings, rankings, and storylines.

        Args:
            game: Game data dictionary
            standings_lookup: Standings lookup dictionary

        Returns:
            Formatted game string
        """
        away_team = game.get("awayTeam", {})
        home_team = game.get("homeTeam", {})

        # Extract team info
        away_tricode = away_team.get("teamTricode", "")
        home_tricode = home_team.get("teamTricode", "")
        away_wins = away_team.get("wins", 0)
        away_losses = away_team.get("losses", 0)
        home_wins = home_team.get("wins", 0)
        home_losses = home_team.get("losses", 0)

        # Format game time
        game_time = self.format_time(game.get("gameTimeEst", ""))

        # Check for national broadcaster
        broadcasters = game.get("broadcasters", {})
        national_broadcasters = broadcasters.get("nationalBroadcasters", [])

        broadcaster_text = ""
        if national_broadcasters and len(national_broadcasters) > 0:
            broadcaster_display = national_broadcasters[0].get("broadcasterDisplay", "")
            if broadcaster_display:
                broadcaster_text = f" | {get_broadcaster_emoji(broadcaster_display)}"

        # Build game header
        game_text = (
            f"{away_tricode} ({away_wins}-{away_losses}) :_{away_tricode.lower()}: at "
        )
        game_text += f"{home_tricode} ({home_wins}-{home_losses}) :_{home_tricode.lower()}: | {game_time}{broadcaster_text}\n"

        # Add standings lines
        away_standings_line = self._format_team_standings_line(
            away_team.get("teamId"), away_tricode, standings_lookup
        )
        home_standings_line = self._format_team_standings_line(
            home_team.get("teamId"), home_tricode, standings_lookup
        )

        game_text += away_standings_line
        game_text += home_standings_line

        # Add rankings - Team stats first (away, then home)
        game_text += self._format_team_rankings(away_team.get("teamId"), away_tricode)
        game_text += self._format_team_rankings(home_team.get("teamId"), home_tricode)

        # Then player stats (away, then home)
        game_text += self._format_player_rankings(away_tricode)
        game_text += self._format_player_rankings(home_tricode)

        # Add pregame storylines
        # game_id = game.get("gameId")
        # if game_id:
        #     storylines = self._get_storylines(game_id)
        #     for storyline in storylines:
        #         game_text += f":t10: {storyline}\n"

        # Add footer sections
        game_text += ":notable: NOTABLES\n"
        game_text += ":mst: MILESTONES\n"
        game_text += ":gtd: GTD/QUESTIONABLE\n"
        game_text += ":out: INJURIES\n"

        return game_text

    # def _get_storylines(self, game_id: str) -> list:
    #     """
    #     Fetch pregame storylines for a specific game.

    #     Args:
    #         game_id: Game ID

    #     Returns:
    #         List of storyline strings
    #     """
    #     try:
    #         # Add small delay to be respectful to API
    #         time.sleep(0.5)

    #         data = self.nba_client.get_pregame_storylines(game_id, storyline_count=10)

    #         # Extract storylines from response
    #         if isinstance(data, dict) and "stories" in data:
    #             return data["stories"]

    #         return []

    #     except Exception as e:
    #         print(f"Warning: Could not fetch storylines for game {game_id}: {e}")
    #         return []
