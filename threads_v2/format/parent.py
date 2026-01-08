"""
Parent message formatter for threads_v2.

Formats the concise parent message (similar to #daily-threads style):
- Matchup with records and seed
- Game time and broadcaster
- Basic streak and L10
- Top 10 rankings bullets
"""

from ..nba.models import GameData, RankingData
from ..config.emojis import get_team_emoji, get_broadcaster_emoji, get_section_emoji
from ..config.labels import LABELS


def format_parent_message(game: GameData) -> str:
    """
    Format a concise parent message for a game.

    Args:
        game: GameData object with all game information

    Returns:
        Formatted plain text string for Slack
    """
    lines = []

    # Game header: #Seed TEAM (W-L) :emoji: at #Seed TEAM (W-L) :emoji: | Time | Broadcaster
    away = game.away_team
    home = game.home_team

    header = (
        f"#{away.playoff_rank} {away.team_tricode} ({away.record}) "
        f"{get_team_emoji(away.team_tricode)} {LABELS['at']} "
        f"#{home.playoff_rank} {home.team_tricode} ({home.record}) "
        f"{get_team_emoji(home.team_tricode)} | {game.game_time_str}"
    )

    if game.national_broadcaster:
        header += f" | {get_broadcaster_emoji(game.national_broadcaster.name)}"

    lines.append(header)

    # Away team streak/L10
    away_line = f"{get_team_emoji(away.team_tricode)} {away.streak} | {LABELS['l10']}: {away.l10}"
    lines.append(away_line)

    # Home team streak/L10
    home_line = f"{get_team_emoji(home.team_tricode)} {home.streak} | {LABELS['l10']}: {home.l10}"
    lines.append(home_line)

    # Top 10 rankings (team rankings only for parent - concise)
    team_rankings = _format_team_rankings_concise(game)
    if team_rankings:
        lines.extend(team_rankings)

    # Top 10 player rankings (brief - just names and stats)
    player_rankings = _format_player_rankings_concise(game)
    if player_rankings:
        lines.extend(player_rankings)

    # Section placeholders for parent (brief)
    lines.append(f"{get_section_emoji('notable')} {LABELS.get('notables', 'NOTABLES')}")
    lines.append(f"{get_section_emoji('milestone')} {LABELS.get('milestones', 'MILESTONES')}")

    # Brief injury summary
    gtd_injuries = game.get_gtd_injuries()
    out_injuries = game.get_out_injuries()

    if gtd_injuries:
        gtd_names = ", ".join(inj.player_name for inj in gtd_injuries)
        lines.append(f"{get_section_emoji('gtd')} {gtd_names}")
    else:
        lines.append(f"{get_section_emoji('gtd')} GTD/QUESTIONABLE")

    if out_injuries:
        out_names = ", ".join(inj.player_name for inj in out_injuries)
        lines.append(f"{get_section_emoji('out')} {out_names}")
    else:
        lines.append(f"{get_section_emoji('out')} INJURIES")

    return "\n".join(lines)


def _format_team_rankings_concise(game: GameData) -> list[str]:
    """Format team rankings in concise format for parent message."""
    lines = []

    for team in [game.away_team, game.home_team]:
        team_ranks = [
            r for r in game.team_rankings if r.team_tricode == team.team_tricode
        ]

        if not team_ranks:
            continue

        # Group by stat type for cleaner output
        basic_stats = []
        advanced_stats = []

        basic_stat_names = {"PPG", "FG%", "3P%", "AST", "REB", "STL", "BLK", "Opp PPG"}
        advanced_stat_names = {"Net RTG", "Off RTG", "Def RTG"}

        for rank in team_ranks:
            stat_text = f"#{rank.rank} in {rank.stat} ({rank.value:.1f})"
            if rank.stat in basic_stat_names:
                basic_stats.append(stat_text)
            elif rank.stat in advanced_stat_names:
                advanced_stats.append(stat_text)

        if basic_stats:
            lines.append(
                f"{get_section_emoji('top10')} {team.team_tricode} {LABELS['ranks']} {', '.join(basic_stats)}"
            )

        if advanced_stats:
            lines.append(
                f"{get_section_emoji('top10')} {team.team_tricode} {LABELS['ranks']} {', '.join(advanced_stats)}"
            )

    return lines


def _format_player_rankings_concise(game: GameData) -> list[str]:
    """Format player rankings in concise format for parent message."""
    lines = []

    for team in [game.away_team, game.home_team]:
        team_player_ranks = [
            r for r in game.player_rankings if r.team_tricode == team.team_tricode
        ]

        if not team_player_ranks:
            continue

        # Group by player
        players_dict: dict[str, list[RankingData]] = {}
        for rank in team_player_ranks:
            if rank.name not in players_dict:
                players_dict[rank.name] = []
            players_dict[rank.name].append(rank)

        for player_name, ranks in players_dict.items():
            # Separate per-game stats from totals
            regular_stats = []
            totals_stats = []

            for rank in ranks:
                # Percentage stats need formatting
                if rank.stat in ("FG%", "3P%"):
                    value_str = f"{rank.value * 100:.1f}"
                elif rank.stat in ("Double Doubles", "Triple Doubles"):
                    value_str = f"{rank.value:.0f}"
                    totals_stats.append(f"#{rank.rank} in {rank.stat} ({value_str})")
                    continue
                else:
                    value_str = f"{rank.value:.1f}"

                regular_stats.append(f"#{rank.rank} in {rank.stat} ({value_str})")

            if regular_stats:
                lines.append(
                    f"{get_section_emoji('top10')} {player_name} ({team.team_tricode}) {LABELS['ranks']} {', '.join(regular_stats)}"
                )

            if totals_stats:
                lines.append(
                    f"{get_section_emoji('top10')} {player_name} ({team.team_tricode}) {LABELS['ranks']} {', '.join(totals_stats)}"
                )

    return lines
