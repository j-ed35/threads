import argparse
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime

from src.config import Config, season_for
from src.formatter import GameFormatter, games_on, index_standings
from src.injuries import index_injuries
from src.milestones import MilestonesChecker
from src.nba_api import NBAClient
from src.rankings import RankingsChecker
from src.slack_client import SlackClient

HEADER_EMOJI = ":nba:"


def main():
    parser = argparse.ArgumentParser(description="Post NBA game threads to Slack (default: #ed-testing)")
    parser.add_argument("--daily_threads", action="store_true", help="Post to #daily-threads")
    parser.add_argument("--mookie", action="store_true", help="Post to #Mookie-Blaylock (injuries + milestones)")
    parser.add_argument("--date", help="Target date in M-D-YY format (e.g. 3-21-26). Defaults to today.")
    args = parser.parse_args()

    started = time.perf_counter()
    channel_name = "#Mookie-Blaylock" if args.mookie else "#daily-threads" if args.daily_threads else "#ed-testing"
    channel_id, settings = Config.channel(channel_name)

    day = datetime.strptime(args.date, "%m-%d-%y").date() if args.date else date.today()
    date_str = f"{day.month}-{day.day}-{day:%y}"
    season = season_for(day)
    nba = NBAClient()
    slack = SlackClient(channel_id)

    print(f"Loading {season} schedule, standings, rankings for {date_str} ({channel_name})...")
    rankings = RankingsChecker(nba)
    with ThreadPoolExecutor(max_workers=4) as executor:
        schedule = executor.submit(nba.get_schedule, season)
        standings = executor.submit(nba.get_standings, season)
        injuries = executor.submit(nba.get_injuries) if settings.include_injuries else None
        rankings_loaded = executor.submit(rankings.load, season)

        games = games_on(schedule.result(), day)
        if not games:
            print(f"No games scheduled for {date_str}")
            slack.send_message(f"No NBA games scheduled for {date_str}")
            return

        milestones = None
        if settings.include_milestones:
            milestones = MilestonesChecker(nba, season)
            # Rankings keep loading in the background meanwhile.
            milestones.load(g[side]["teamId"] for g in games for side in ("awayTeam", "homeTeam"))

        rankings_loaded.result()
        try:
            standings_index = index_standings(standings.result())
        except Exception as e:
            print(f"Warning: could not fetch standings, posting without seeds/records: {e}")
            standings_index = {}
        injuries_index = index_injuries(injuries.result()) if injuries else None

    formatter = GameFormatter(rankings, standings_index, injuries_index, milestones)
    formatted = [formatter.format_game(g) for g in games]
    print(f"Fetched in {time.perf_counter() - started:.1f}s with {NBAClient.call_count} NBA API calls")

    game_word = "Game" if len(formatted) == 1 else "Games"
    slack.send_message(f"{HEADER_EMOJI} {len(formatted)} {game_word} for {date_str}")
    slack.send_message("———")
    slack.send_message("———")
    for i, game in enumerate(formatted, 1):
        slack.send_game_with_thread(game["parent"], game["thread"], game["injury_thread"])
        replies = "+".join(k for k in ("thread", "injury_thread") if game[k]) or "no replies"
        print(f"Game {i}/{len(formatted)} sent ({replies})")
    print(f"✓ Posted {len(formatted)} games to {channel_name} in {time.perf_counter() - started:.1f}s")


if __name__ == "__main__":
    main()
