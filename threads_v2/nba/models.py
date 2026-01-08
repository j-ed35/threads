"""
Data models for NBA game data.

These models represent the structured game data used throughout threads_v2.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class TeamData:
    """Represents a team in a game."""

    team_id: int
    team_tricode: str
    team_name: str
    wins: int
    losses: int
    playoff_rank: int = 0
    streak: str = ""
    l10: str = ""
    home_record: str = ""
    road_record: str = ""
    l10_home: str = ""
    l10_road: str = ""
    monthly_records: dict = field(default_factory=dict)

    @property
    def record(self) -> str:
        """Get formatted win-loss record."""
        return f"{self.wins}-{self.losses}"


@dataclass
class BroadcasterData:
    """Represents a broadcaster for a game."""

    name: str
    display: str


@dataclass
class InjuryData:
    """Represents an injury for a player."""

    player_name: str
    status: str  # "GTD", "OUT", "QUESTIONABLE", "DOUBTFUL"
    injury_type: str
    team_tricode: str


@dataclass
class RankingData:
    """Represents a ranking (team or player)."""

    name: str  # Team or player name
    team_tricode: str
    stat: str  # Friendly stat name (e.g., "PPG", "AST")
    rank: int
    value: float


@dataclass
class StandingsData:
    """Represents standings data for a team."""

    team_id: int
    team_tricode: str
    playoff_rank: int
    streak: str
    l10: str
    home_record: str
    road_record: str
    l10_home: str
    l10_road: str
    monthly_records: dict = field(default_factory=dict)


@dataclass
class GameData:
    """Represents a single NBA game with all associated data."""

    game_id: str
    game_time: datetime
    game_time_str: str  # Formatted time string (e.g., "7:30 PM ET")
    away_team: TeamData
    home_team: TeamData
    national_broadcaster: Optional[BroadcasterData] = None

    # Rankings (populated after initial fetch)
    team_rankings: list[RankingData] = field(default_factory=list)
    player_rankings: list[RankingData] = field(default_factory=list)

    # Injuries (populated after initial fetch)
    injuries: list[InjuryData] = field(default_factory=list)

    @property
    def matchup(self) -> str:
        """Get formatted matchup string."""
        return f"{self.away_team.team_tricode} at {self.home_team.team_tricode}"

    def get_gtd_injuries(self) -> list[InjuryData]:
        """Get all GTD/Questionable/Doubtful injuries for this game."""
        return [
            inj
            for inj in self.injuries
            if inj.status.upper() in ("GTD", "QUESTIONABLE", "DOUBTFUL")
        ]

    def get_out_injuries(self) -> list[InjuryData]:
        """Get all OUT injuries for this game."""
        return [inj for inj in self.injuries if inj.status.upper() == "OUT"]

    def get_team_rankings(self, team_tricode: str) -> list[RankingData]:
        """Get team rankings for a specific team."""
        return [
            r
            for r in self.team_rankings
            if r.team_tricode == team_tricode and r.name == team_tricode
        ]

    def get_player_rankings(self, team_tricode: str) -> list[RankingData]:
        """Get player rankings for a specific team."""
        return [r for r in self.player_rankings if r.team_tricode == team_tricode]
