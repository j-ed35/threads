"""
Streaks provider stub for threads_v2.

This is a Phase 2 placeholder. In Phase 1, this returns empty results.

Phase 2 Integration Notes:
--------------------------
The streaks system will integrate with the streak_finder repository at:
    /Users/jacobederer/Repositories/streak_finder

That project uses:
- SQL queries against an NBA stats database
- YAML-driven streak definitions (configurable without code changes)
- Support for team streaks, player streaks, and matchup-specific streaks

To integrate in Phase 2:
1. Add streak_finder as a dependency or import path
2. Load YAML streak definitions from streak_finder/definitions/
3. Call streak_finder's query engine with game context
4. Transform results into StreakItem objects

Example YAML streak definition format (from streak_finder):
```yaml
streaks:
  - name: "points_streak"
    description: "Player scoring 20+ points"
    sql: |
      SELECT player_name, COUNT(*) as games
      FROM game_stats
      WHERE pts >= 20
      GROUP BY player_id
      HAVING games >= 5
    threshold: 5
```
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..nba.models import GameData


@dataclass
class StreakItem:
    """
    Represents a streak to display.

    Attributes:
        player_name: Name of player (or team name for team streaks)
        team_tricode: Team abbreviation
        streak_type: Type of streak (e.g., "points", "wins", "double_double")
        description: Human-readable description for display
        games_count: Number of games in the streak
        stat_value: Optional stat value (e.g., average points during streak)
    """

    player_name: str
    team_tricode: str
    streak_type: str
    description: str
    games_count: int
    stat_value: float | None = None


def get_streaks_for_game(game: "GameData") -> list[StreakItem]:
    """
    Get relevant streaks for a game.

    In Phase 1, this returns an empty list.
    In Phase 2, this will query the streak_finder database.

    Args:
        game: GameData object containing team and player information

    Returns:
        List of StreakItem objects for display

    TODO (Phase 2):
        - Import streak_finder module
        - Load streak definitions from YAML
        - Query streaks for:
            - Away team players
            - Home team players
            - Team vs team matchup history
            - Players vs specific opponent
        - Filter to most interesting/relevant streaks
        - Return sorted by significance

    Integration point:
        /Users/jacobederer/Repositories/streak_finder
    """
    # Phase 1: Return empty list - streaks will be added in Phase 2
    return []


def get_team_streaks(team_id: int) -> list[StreakItem]:
    """
    Get team-level streaks.

    TODO (Phase 2): Implement using streak_finder
    """
    return []


def get_player_streaks(player_id: int) -> list[StreakItem]:
    """
    Get player-level streaks.

    TODO (Phase 2): Implement using streak_finder
    """
    return []


def get_matchup_streaks(away_team_id: int, home_team_id: int) -> list[StreakItem]:
    """
    Get matchup-specific streaks (e.g., "Lakers have won 5 straight vs Celtics").

    TODO (Phase 2): Implement using streak_finder
    """
    return []
