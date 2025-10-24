from datetime import datetime
from .broadcaster_mapping import get_broadcaster_emoji


class GameFormatter:
    @staticmethod
    def format_time(game_time_est):
        """Convert ISO time to readable format"""
        try:
            dt = datetime.fromisoformat(game_time_est.replace("Z", "+00:00"))
            return dt.strftime("%I:%M %p ET").lstrip("0")
        except:
            return "TBD"

    @staticmethod
    def format_games(data):
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
            # Note: Using 'awayTeam' instead of 'visitorTeam' for leagueSchedule
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

            # Format with records and emoji placeholders
            game_line = f"{away_tricode} ({away_wins}-{away_losses}) :_{away_tricode}: at {home_tricode} ({home_wins}-{home_losses}) :_{home_tricode}: | {game_time}{broadcaster_text}"

            # Add the required subtext lines
            subtext = """
:reminder_ribbon: REMINDER
:t20: MILESTONES
:GTD: GTD/QUESTIONABLE
:out: INJURIES"""

            formatted_games.append(f"{game_line}\n{subtext}\n")

        return "\n".join(formatted_games)
