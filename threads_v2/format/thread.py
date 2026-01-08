"""
Thread reply formatter for threads_v2.

Formats the comprehensive threaded reply (similar to #ed-testing style):
- Extended standings with home/away splits
- Monthly records
- Full injury details
- Additional stat categories
"""

from ..nba.models import GameData, RankingData, InjuryData
from ..config.emojis import get_team_emoji, get_broadcaster_emoji, get_section_emoji
from ..config.labels import LABELS, MONTHS
from ..streaks import get_streaks_for_game


def format_thread_message(game: GameData) -> str:
    """
    Format a comprehensive thread reply for a game.

    Args:
        game: GameData object with all game information

    Returns:
        Formatted plain text string for Slack thread reply
    """
    lines = []

    # Thread header
    lines.append(f"*Detailed Preview: {game.away_team.team_tricode} @ {game.home_team.team_tricode}*")
    lines.append("")

    # Extended standings for away team
    away_standings = _format_team_extended_standings(game.away_team, is_home=False)
    lines.extend(away_standings)

    # Extended standings for home team
    home_standings = _format_team_extended_standings(game.home_team, is_home=True)
    lines.extend(home_standings)

    # Monthly records
    lines.append("")
    lines.extend(_format_monthly_records(game))

    # Misc team rankings (if any)
    misc_rankings = _format_misc_rankings(game)
    if misc_rankings:
        lines.append("")
        lines.extend(misc_rankings)

    # Streaks section (Phase 2 - currently stub)
    streaks = get_streaks_for_game(game)
    if streaks:
        lines.append("")
        lines.append(f"*{get_section_emoji('streak')} STREAKS*")
        for streak in streaks:
            lines.append(f"• {streak.description}")

    # Detailed injury report
    lines.append("")
    lines.extend(_format_detailed_injuries(game))

    # Section placeholders
    lines.append("")
    lines.append(f"{get_section_emoji('notable')} *NOTABLES*")
    lines.append("_Add notable storylines here_")

    lines.append("")
    lines.append(f"{get_section_emoji('milestone')} *MILESTONES*")
    lines.append("_Add milestone watch items here_")

    return "\n".join(lines)


def _format_team_extended_standings(team, is_home: bool) -> list[str]:
    """Format extended standings for a team."""
    lines = []

    emoji = get_team_emoji(team.team_tricode)

    # First line: streak, L10, home/away record
    if is_home:
        line1 = (
            f"{emoji} {team.streak} | "
            f"{LABELS['l10']}: {team.l10}, "
            f"{LABELS['home']}: {team.home_record} | "
            f"{LABELS['l10']}: {team.l10_home}"
        )
    else:
        line1 = (
            f"{emoji} {team.streak} | "
            f"{LABELS['l10']}: {team.l10}, "
            f"{LABELS['away']}: {team.road_record} | "
            f"{LABELS['l10']}: {team.l10_road}"
        )

    lines.append(line1)

    return lines


def _format_monthly_records(game: GameData) -> list[str]:
    """Format monthly records for both teams."""
    lines = []

    for team in [game.away_team, game.home_team]:
        if not team.monthly_records:
            continue

        emoji = get_team_emoji(team.team_tricode)

        # Build monthly parts in order
        month_parts = []
        for month in MONTHS:
            record = team.monthly_records.get(month, "")
            if record:
                month_parts.append(f"{month.upper()}: {record}")

        if month_parts:
            lines.append(f"{emoji} {', '.join(month_parts)}")

    return lines


def _format_misc_rankings(game: GameData) -> list[str]:
    """Format miscellaneous team rankings (points off turnovers, etc.)."""
    lines = []

    misc_stat_names = {"PTS Off TOV", "PTS 2nd Chance", "PTS Fast Break", "PTS Paint"}

    for team in [game.away_team, game.home_team]:
        team_ranks = [
            r
            for r in game.team_rankings
            if r.team_tricode == team.team_tricode and r.stat in misc_stat_names
        ]

        if not team_ranks:
            continue

        stat_parts = [
            f"#{r.rank} in {r.stat} ({r.value:.1f})" for r in team_ranks
        ]

        if stat_parts:
            lines.append(
                f"{get_section_emoji('top10')} {team.team_tricode} {LABELS['ranks']} {', '.join(stat_parts)}"
            )

    return lines


def _format_detailed_injuries(game: GameData) -> list[str]:
    """Format detailed injury information for thread."""
    lines = []

    gtd_injuries = game.get_gtd_injuries()
    out_injuries = game.get_out_injuries()

    # GTD/Questionable section
    lines.append(f"{get_section_emoji('gtd')} *GTD/QUESTIONABLE*")
    if gtd_injuries:
        for inj in gtd_injuries:
            emoji = get_team_emoji(inj.team_tricode)
            lines.append(f"{emoji} {inj.player_name} - {inj.injury_type} ({inj.status})")
    else:
        lines.append("_None reported_")

    # OUT section
    lines.append("")
    lines.append(f"{get_section_emoji('out')} *OUT*")
    if out_injuries:
        for inj in out_injuries:
            emoji = get_team_emoji(inj.team_tricode)
            lines.append(f"{emoji} {inj.player_name} - {inj.injury_type} ({inj.status})")
    else:
        lines.append("_None reported_")

    return lines


def _format_full_injury_report(games: list[GameData]) -> list[str]:
    """Format a full injury report across all games (for standalone message)."""
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("*Full Injury Report*")

    for game in games:
        all_injuries = game.injuries
        if not all_injuries:
            continue

        away_tricode = game.away_team.team_tricode
        home_tricode = game.home_team.team_tricode

        lines.append("")
        lines.append(
            f"{away_tricode} {get_team_emoji(away_tricode)} @ "
            f"{home_tricode} {get_team_emoji(home_tricode)}"
        )

        for inj in all_injuries:
            emoji = get_team_emoji(inj.team_tricode)
            lines.append(f"{emoji} {inj.player_name} - {inj.injury_type} ({inj.status})")

    if len(lines) <= 2:
        return []  # No injuries to report

    return lines
