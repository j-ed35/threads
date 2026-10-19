"""
Post a night's final scores plus both conference standings to #Mookie-Blaylock.

Usage:
    uv run python scores.py            # last night's games (before 6 AM) or today's
    uv run python scores.py 10-20-26   # a specific date (M-D-YY)

Shell shortcut: `nba mookie scores`, `nba mookie scores 10-20-26`
"""

import argparse
from datetime import date, datetime, timedelta

from src.config import Config, season_for
from src.formatter import games_on
from src.nba_api import NBAClient
from src.slack_client import SlackClient

# Runs before this hour count as the previous night: games end around 1-1:30 AM ET.
NEW_DAY_HOUR = 6

# AP-style month abbreviations, e.g. "TUESDAY, JAN. 27".
MONTHS = ["JAN.", "FEB.", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUG.", "SEPT.", "OCT.", "NOV.", "DEC."]


def default_day(now: datetime) -> date:
    return (now - timedelta(days=1)).date() if now.hour < NEW_DAY_HOUR else now.date()


def score_line(game: dict) -> str:
    """`POR 111 - 115 WAS`, with an OT tag, live clock, tip time or postponement as needed."""
    away, home = game.get("awayTeam", {}), game.get("homeTeam", {})
    away_tri, home_tri = away.get("teamTricode", ""), home.get("teamTricode", "")
    status, text = game.get("gameStatus"), game.get("gameStatusText", "").strip()
    if game.get("postponedStatus") == "Y":
        return f"{away_tri} - {home_tri} (Postponed)"
    if status == 1:
        return f"{away_tri} - {home_tri} ({text})"
    line = f"{away_tri} {away.get('score', 0)} - {home.get('score', 0)} {home_tri}"
    if status == 3:
        # "Final/OT" -> (OT), "Final/OT2" -> (2OT)
        ot = text.partition("/")[2]
        return f"{line} ({ot[2:] + 'OT' if ot[2:] else ot})" if ot else line
    return f"{line} ({text})"


def conference_lines(teams: list, conference: str) -> list:
    """Seeded standings for one conference, with lines after the 6th (playoff) and 10th (play-in) seeds."""
    seeded = sorted(
        (t for t in teams if t.get("conference") == conference and t.get("playoffRank")),
        key=lambda t: t["playoffRank"],
    )
    lines = [f"{conference}ern Conference"]
    for t in seeded:
        tri = t.get("teamAbbreviation", "")
        lines.append(f"#{t['playoffRank']} :_{tri.lower()}: {tri} ({t.get('wins', 0)}-{t.get('losses', 0)})")
        if t["playoffRank"] == 6:
            lines.append("___")
        elif t["playoffRank"] == 10:
            lines.append("====")
    return lines


def build_message(games: list, standings: dict, day: date) -> str:
    teams = standings.get("leagueStandings", {}).get("teams", [])
    lines = ["SCORES", f"{day:%A}".upper() + f", {MONTHS[day.month - 1]} {day.day}", ""]
    lines += [score_line(g) for g in games] or ["No NBA games"]
    lines.append("")
    lines += conference_lines(teams, "East")
    lines += conference_lines(teams, "West")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Post a night's NBA scores and standings to #Mookie-Blaylock")
    parser.add_argument("date", nargs="?", help=f"M-D-YY; defaults to last night before {NEW_DAY_HOUR} AM, else today")
    args = parser.parse_args()

    channel_id, _ = Config.channel(
        "#Mookie-Blaylock", keys=("NBA_API_KEY", "NBA_STANDINGS_KEY", "SLACK_BOT_TOKEN")
    )
    day = datetime.strptime(args.date, "%m-%d-%y").date() if args.date else default_day(datetime.now())
    season = season_for(day)
    nba = NBAClient()

    print(f"Fetching {day:%-m-%-d-%y} scores and {season} standings...")
    message = build_message(games_on(nba.get_schedule(season), day), nba.get_standings(season), day)
    print(message)
    SlackClient(channel_id).send_message(message)
    print("\n✓ Posted to #Mookie-Blaylock")


if __name__ == "__main__":
    main()
