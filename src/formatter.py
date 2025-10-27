from datetime import datetime
from .broadcaster_mapping import get_broadcaster_emoji
import time


class GameFormatter:
    def __init__(self, nba_client=None):
        """Initialize formatter with optional NBA client for fetching storylines"""
        self.nba_client = nba_client

    @staticmethod
    def format_time(game_time_est):
        """Convert ISO time to readable format"""
        try:
            dt = datetime.fromisoformat(game_time_est.replace("Z", "+00:00"))
            return dt.strftime("%I:%M %p ET").lstrip("0")
        except:
            return "TBD"

    def format_storylines(self, game_id):
        """Fetch and format storylines for a game"""
        if not self.nba_client:
            return ""

        storylines_data = self.nba_client.get_pregame_storylines(
            game_id, storyline_count=10
        )

        if not storylines_data:
            return ""

        # Extract stories array from response
        stories = storylines_data.get("stories", [])

        if not stories:
            return ""

        # Format each storyline with ribbon emoji
        formatted = [f":reminder_ribbon: {story}" for story in stories]

        return "\n".join(formatted)

    def format_games(self, data):
        """Format games into desired output"""
        if not data or "leagueSchedule" not in data:
            return None

        league_schedule = data["leagueSchedule"]
        if not league_schedule or "gameDates" not in league_schedule:
            return None

        game_dates = league_schedule["gameDates"]
        if not game_dates:
            return None

        # Get today's date in MM/DD/YYYY format (matches API format)
        today = datetime.now().strftime("%m/%d/%Y")
        todays_games = None

        for game_date in game_dates:
            # API returns "MM/DD/YYYY HH:MM:SS" - extract just the date part
            game_date_str = game_date.get("gameDate", "")
            date_only = (
                game_date_str.split()[0] if " " in game_date_str else game_date_str
            )

            if date_only == today:
                todays_games = game_date.get("games", [])
                break

        if not todays_games:
            return None

        formatted_games = []
        for game in todays_games:
            away_team = game.get("awayTeam", {})
            home_team = game.get("homeTeam", {})

            away_tricode = away_team.get("teamTricode", "TBD")
            home_tricode = home_team.get("teamTricode", "TBD")

            # Get team records (wins-losses)
            away_wins = away_team.get("wins", 0)
            away_losses = away_team.get("losses", 0)
            home_wins = home_team.get("wins", 0)
            home_losses = home_team.get("losses", 0)

            game_time = GameFormatter.format_time(game.get("gameTimeEst", ""))

            # Check for national broadcaster
            broadcasters = game.get("broadcasters", {})
            national_broadcasters = broadcasters.get("nationalBroadcasters", [])

            broadcaster_text = ""
            if national_broadcasters and len(national_broadcasters) > 0:
                broadcaster_display = national_broadcasters[0].get(
                    "broadcasterDisplay", ""
                )
                if broadcaster_display:
                    broadcaster_text = f", {get_broadcaster_emoji(broadcaster_display)}"

            # Format game line
            game_line = f"{away_tricode} ({away_wins}-{away_losses}) :_{away_tricode}: at {home_tricode} ({home_wins}-{home_losses}) :_{home_tricode}: | {game_time}{broadcaster_text}"

            # Fetch storylines for this game
            game_id = game.get("gameId")
            storylines_text = ""
            if game_id and self.nba_client:
                storylines_text = self.format_storylines(game_id)
                # Add small delay to be courteous to API
                time.sleep(0.5)

            # Build the complete game block
            game_block = game_line
            if storylines_text:
                game_block += f"\n{storylines_text}"

            # Add remaining subtext lines
            game_block += """
:t20: MILESTONES
:GTD: GTD/QUESTIONABLE
:out: INJURIES"""

            formatted_games.append(game_block + "\n")

        return "\n".join(formatted_games)
