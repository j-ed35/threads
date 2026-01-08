"""
CLI entry point for threads_v2.

Usage:
    uv run python -m threads_v2.run --channel ed_testing
    uv run python -m threads_v2.run --channel ed_testing --dry-run

Options:
    --channel, -c: Target channel (ed_testing, mookie, daily_threads, or channel ID)
    --dry-run: Print messages without posting to Slack
    --verbose, -v: Enable verbose logging
"""

import argparse
import sys
from datetime import date
from pathlib import Path

# Add parent directory to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables before other imports
load_dotenv()

from threads_v2.util.logging import setup_logging, log_run_start, log_run_end
from threads_v2.nba.client import NBAClientV2
from threads_v2.slack.client import SlackClientV2, SlackAPIError
from threads_v2.format.parent import format_parent_message
from threads_v2.format.thread import format_thread_message
from threads_v2.format.blocks import build_blocks_for_message


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="NBA Daily Threads Bot V2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Post to #ed-testing channel
    uv run python -m threads_v2.run --channel ed_testing

    # Dry run (print without posting)
    uv run python -m threads_v2.run --channel ed_testing --dry-run

    # Use a specific channel ID
    uv run python -m threads_v2.run --channel C0123456789
        """,
    )

    parser.add_argument(
        "--channel",
        "-c",
        default="ed_testing",
        help="Target channel: ed_testing, mookie, daily_threads, or channel ID (default: ed_testing)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print messages without posting to Slack",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--no-blocks",
        action="store_true",
        help="Use plain text only (no Block Kit)",
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Set up logging
    import logging

    level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(level=level)

    log_run_start(logger, args.channel)

    games_processed = 0
    success = False

    try:
        # Initialize NBA client
        logger.info("Initializing NBA client...")
        nba = NBAClientV2()
        nba.validate_config()

        # Fetch today's games
        logger.info("Fetching today's games...")
        games = nba.get_todays_games()

        if not games:
            logger.info("No games scheduled for today")
            print("No NBA games scheduled for today")

            if not args.dry_run:
                slack = SlackClientV2()
                channel_id = slack.get_channel_id(args.channel)
                slack.post_message(channel_id, "No NBA games scheduled for today")

            success = True
            log_run_end(logger, 0, success)
            return 0

        logger.info(f"Found {len(games)} games")

        # Initialize Slack client (unless dry run)
        slack = None
        channel_id = None

        if not args.dry_run:
            logger.info("Initializing Slack client...")
            slack = SlackClientV2()

            # Test connection
            auth_info = slack.test_connection()
            logger.info(f"Connected as: {auth_info.get('user')} in {auth_info.get('team')}")

            channel_id = slack.get_channel_id(args.channel)
            logger.info(f"Target channel ID: {channel_id}")

        # Process each game
        today_str = date.today().strftime("%m/%d/%Y")
        print(f"\n{'=' * 60}")
        print(f"NBA Games - {today_str}")
        print(f"{'=' * 60}")

        for i, game in enumerate(games, 1):
            logger.info(f"Processing game {i}/{len(games)}: {game.matchup}")

            # Format messages
            parent_text = format_parent_message(game)
            thread_text = format_thread_message(game)

            # Build blocks (optional)
            parent_blocks = None
            thread_blocks = None
            if not args.no_blocks:
                parent_blocks = build_blocks_for_message(parent_text)
                thread_blocks = build_blocks_for_message(thread_text)

            if args.dry_run:
                # Print to console
                print(f"\n--- Game {i}/{len(games)} ---")
                print("\n[PARENT MESSAGE]")
                print(parent_text)
                print("\n[THREAD REPLY]")
                print(thread_text)
            else:
                # Post to Slack
                try:
                    parent_ts, thread_ts = slack.post_game_with_thread(
                        channel_id=channel_id,
                        parent_text=parent_text,
                        thread_text=thread_text,
                        parent_blocks=parent_blocks,
                        thread_blocks=thread_blocks,
                    )
                    logger.info(f"Posted game {i}/{len(games)}: parent_ts={parent_ts}, thread_ts={thread_ts}")
                    print(f"Game {i}/{len(games)} posted: {game.matchup}")

                except SlackAPIError as e:
                    logger.error(f"Slack error posting game {i}: {e}")
                    print(f"Error posting game {i}: {e}")
                    # Continue with other games

            games_processed += 1

        success = True
        print(f"\n{'=' * 60}")
        print(f"Completed: {games_processed}/{len(games)} games processed")
        if args.dry_run:
            print("(Dry run - no messages posted)")
        print(f"{'=' * 60}")

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Error: {e}")
        return 1

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"Error: {e}")
        return 1

    finally:
        log_run_end(logger, games_processed, success)

    return 0


if __name__ == "__main__":
    sys.exit(main())
