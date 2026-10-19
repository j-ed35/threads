"""
Post the all-time NBA regular-season career leaders for a stat to #Mookie-Blaylock.

Usage:
    uv run python leaders.py AST        # top 20 all-time assists
    uv run python leaders.py -PTS       # leading dash is fine too
    uv run python leaders.py REB -n 10  # custom count
    uv run python leaders.py TD3        # top 10 all-time triple-doubles
    uv run python leaders.py PTS --csv  # write $ALL_TIME_LISTS_DIR/nba_points_leaders.csv instead

Shell shortcut: `nba mookie ast`, `nba mookie pts csv`, ...
"""

import argparse
import csv
import os
import sys

from src.config import Config
from src.nba_api import NBAClient
from src.slack_client import SlackClient

# stat tag -> (Measure, sort column / stats key, display label, CSV filename slug)
STATS = {
    "GP": ("BASE_GP", "GP", "Games Played", "games_played"),
    "PTS": ("BASE_PTS", "PTS", "Points", "points"),
    "REB": ("BASE_REB", "REB", "Rebounds", "rebounds"),
    "AST": ("BASE_AST", "AST", "Assists", "assists"),
    "STL": ("BASE_STL", "STL", "Steals", "steals"),
    "BLK": ("BASE_BLK", "BLK", "Blocks", "blocks"),
    "3PM": ("BASE_FG3M", "FG3M", "3-Pointers Made", "threes"),
    "FG3M": ("BASE_FG3M", "FG3M", "3-Pointers Made", "threes"),
    "FGM": ("BASE_FGM", "FGM", "Field Goals Made", "field_goals"),
    "FTM": ("BASE_FTM", "FTM", "Free Throws Made", "free_throws"),
    "OREB": ("BASE_OREB", "OREB", "Offensive Rebounds", "offensive_rebounds"),
    "DREB": ("BASE_DREB", "DREB", "Defensive Rebounds", "defensive_rebounds"),
    "TOV": ("BASE_TOV", "TOV", "Turnovers", "turnovers"),
    "MIN": ("BASE_MIN", "MIN", "Minutes", "minutes"),
    "FG3A": ("BASE_FG3A", "FG3A", "3-Point Attempts", "three_point_attempts"),
    "DD2": ("BASE_DD2", "DD2", "Double-Doubles", "double_doubles"),
    "TD3": ("BASE_TD3", "TD3", "Triple-Doubles", "triple_doubles"),
}

# DD2/TD3 aren't on the career endpoint; the season endpoint with SeasonYear=All has them.
SEASON_ENDPOINT_STATS = {"DD2", "TD3"}

DEFAULT_COUNT = 20
DEFAULT_COUNTS = {"DD2": 15, "TD3": 10}


def fetch_leaders(tag: str, count: int) -> list:
    """Top `count` career leaders for a stat tag as [(name, value)], zero rows dropped."""
    measure, sort_col, _, _ = STATS[tag]
    players = NBAClient().get_career_leaders(
        measure, sort_col, count, season_endpoint=tag in SEASON_ENDPOINT_STATS
    )
    leaders = [(p.get("name", ""), p.get("stats", {}).get(sort_col) or 0) for p in players[:count]]
    return [(name, value) for name, value in leaders if value > 0]


def main():
    parser = argparse.ArgumentParser(description="Post all-time NBA career leaders to #Mookie-Blaylock")
    parser.add_argument("stat", help=f"Stat tag ({', '.join(STATS)}); a leading '-' is ok")
    parser.add_argument("-n", type=int, help=f"Number of leaders (default {DEFAULT_COUNT}; DD2 15, TD3 10)")
    parser.add_argument("--csv", action="store_true", help="Write a CSV to $ALL_TIME_LISTS_DIR instead of posting")
    # argparse would read "-PTS" as an unknown flag, so strip the dash from stat tags first.
    argv = [a.lstrip("-") if a.lstrip("-").upper() in STATS else a for a in sys.argv[1:]]
    args = parser.parse_args(argv)

    tag = args.stat.upper()
    if tag not in STATS:
        raise SystemExit(f"Unknown stat '{tag}'. Valid stats: {', '.join(sorted(STATS))}")
    _, _, label, slug = STATS[tag]
    count = args.n or DEFAULT_COUNTS.get(tag, DEFAULT_COUNT)

    out_dir = os.getenv("ALL_TIME_LISTS_DIR")
    if args.csv and not out_dir:
        raise SystemExit("--csv needs ALL_TIME_LISTS_DIR set (in .env or the environment)")

    if args.csv:
        Config.validate(keys=("QUERY_TOOL_API_KEY",))
    else:
        channel_id, _ = Config.channel("#Mookie-Blaylock", keys=("QUERY_TOOL_API_KEY", "SLACK_BOT_TOKEN"))

    print(f"Fetching all-time top {count} {label}...")
    leaders = fetch_leaders(tag, count)

    if args.csv:
        path = os.path.join(out_dir, f"nba_{slug}_leaders.csv")
        with open(path, "w", newline="") as f:
            csv.writer(f).writerows((name, f"{value:.0f}") for name, value in leaders)
        print(f"✓ Saved {path}")
        return

    lines = [f"*All-Time {label} Leaders*"]
    lines += [f"{rank}. {name} – {value:,.0f}" for rank, (name, value) in enumerate(leaders, start=1)]
    message = "\n".join(lines)
    print(message)
    SlackClient(channel_id).send_message(message)
    print("\n✓ Posted to #Mookie-Blaylock")


if __name__ == "__main__":
    main()
