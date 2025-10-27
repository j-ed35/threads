from src.config import Config
from src.nba_api import NBAClient
from src.formatter import GameFormatter
from src.slack_client import SlackClient


def main():
    try:
        # Validate configuration
        Config.validate()

        # Initialize clients
        nba = NBAClient()
        slack = SlackClient()
        formatter = GameFormatter(nba_client=nba)  # Pass NBA client to formatter

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
