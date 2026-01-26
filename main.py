import argparse

from src.config import Config
from src.nba_api import NBAClient
from src.rankings import RankingsChecker
from src.formatter import GameFormatter
from src.slack_client import SlackClient


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Send NBA game data to Slack")
    parser.add_argument(
        "--ed_testing",
        action="store_true",
        help="Send to #ed-testing channel instead of #daily-threads",
    )
    args = parser.parse_args()

    try:
        # Validate configuration
        Config.validate()

        # Initialize clients
        nba = NBAClient()
        rankings_checker = RankingsChecker()

        # Select channel based on flag (default: daily threads)
        if args.ed_testing:
            channel_id = Config.SLACK_CHANNEL_ID_ED_TESTING
            channel_name = "#ed-testing"
        else:
            channel_id = Config.SLACK_CHANNEL_ID_DAILY_THREADS
            channel_name = "#daily-threads"

        slack = SlackClient(channel_id=channel_id)

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

        # Send each game as parent message with threaded replies
        print(f"Sending {len(formatted_games)} games to Slack ({channel_name})...")
        for i, game_data in enumerate(formatted_games, 1):
            parent_text = game_data["parent"]
            thread_text = game_data["thread"]
            injury_thread = game_data.get("injury_thread")

            result = slack.send_game_with_thread(parent_text, thread_text, injury_thread)

            thread_status = "with thread" if thread_text else "no thread"
            injury_status = "+ injuries" if injury_thread else ""
            print(f"Game {i}/{len(formatted_games)}: sent ({thread_status}{injury_status})")

        print(f"✓ All {len(formatted_games)} games sent successfully!")

    except Exception as e:
        print(f"✗ Error: {e}")
        raise


if __name__ == "__main__":
    main()
