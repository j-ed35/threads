from datetime import datetime


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
        if not data or "rollingSchedule" not in data:
            return None

        rolling_schedule = data["rollingSchedule"]
        if not rolling_schedule or "gameDates" not in rolling_schedule:
            return None

        game_dates = rolling_schedule["gameDates"]
        if not game_dates:
            return None

        today = datetime.now().strftime("%Y-%m-%d")
        todays_games = None

        for game_date in game_dates:
            if game_date.get("gameDate") == today:
                todays_games = game_date.get("games", [])
                break

        if not todays_games:
            return None

        formatted_games = []
        for game in todays_games:
            away_team = game.get("visitorTeam", {})
            home_team = game.get("homeTeam", {})

            away_name = away_team.get("teamTricode", "TBD")
            home_name = home_team.get("teamTricode", "TBD")
            game_time = GameFormatter.format_time(game.get("gameTimeEst", ""))

            formatted_games.append(f"{away_name} at {home_name} | {game_time}")

        return "\n".join(formatted_games)
