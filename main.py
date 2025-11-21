from src.config import Config
from src.nba_api import NBAClient
from src.rankings import RankingsChecker
from src.formatter import GameFormatter
from src.slack_client import SlackClient


def main():
    try:
        # Validate configuration
        Config.validate()

        # Initialize clients
        nba = NBAClient()
        rankings_checker = RankingsChecker()
        slack = SlackClient()
        formatter = GameFormatter(nba_client=nba, rankings_checker=rankings_checker)

        # Load rankings data once
        print("Loading team and player rankings...")
        formatter.load_rankings(season_year="2025-26")

        # Fetch and format games
        print("Fetching today's NBA games...")
        data = nba.get_todays_games()

        print("Fetching storylines for each game...")
        games_text = formatter.format_games(data)

        # Send to Slack
        print("Sending to Slack...")
        result = slack.send_games(games_text)

        print(result)

    except Exception as e:
        print(f"✗ Error: {e}")
        raise


if __name__ == "__main__":
    main()
