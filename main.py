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

        # Use ED_TESTING channel for development (change to DAILY_THREADS for production)
        slack = SlackClient(channel_id=Config.SLACK_CHANNEL_ID_DAILY_THREADS)

        formatter = GameFormatter(nba_client=nba, rankings_checker=rankings_checker)

        # Load rankings data once
        print("Loading team and player rankings...")
        formatter.load_rankings(season_year="2025-26")

        # Fetch games
        print("Fetching today's NBA games...")
        data = nba.get_todays_games()

        # Format games with parent/thread structure
        print("Formatting games...")
        formatted_games = formatter.format_games_with_threads(data)

        if not formatted_games:
            print("No games scheduled for today")
            slack.send_message("No NBA games scheduled for today")
            return

        # Send each game as parent message with threaded reply
        print(f"Sending {len(formatted_games)} games to Slack...")
        for i, game_data in enumerate(formatted_games, 1):
            parent_text = game_data["parent"]
            thread_text = game_data["thread"]

            result = slack.send_game_with_thread(parent_text, thread_text)

            thread_status = "with thread" if thread_text else "no thread"
            print(f"Game {i}/{len(formatted_games)}: sent ({thread_status})")

        print(f"✓ All {len(formatted_games)} games sent successfully!")

    except Exception as e:
        print(f"✗ Error: {e}")
        raise


if __name__ == "__main__":
    main()
