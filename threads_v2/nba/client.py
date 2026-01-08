"""
NBA API client for threads_v2.

Handles fetching schedule, standings, rankings, and injury data from NBA API.
Re-uses the proven API logic from v1 but structures data into V2 models.
"""

import os
import requests
from datetime import datetime
from typing import Optional

from .models import (
    GameData,
    TeamData,
    StandingsData,
    BroadcasterData,
    InjuryData,
    RankingData,
)
from ..util.logging import get_logger

logger = get_logger("threads_v2.nba")


class NBAClientV2:
    """
    NBA API client for fetching game data.

    Uses the same NBA API endpoints as v1 but returns structured data models.
    """

    NBA_API_BASE = "https://api.nba.com/v0"
    LEAGUE_ID = "00"

    # Stats where lower values are better (sorted ascending)
    TEAM_STATS_ASCENDING = {
        "ADV_TM_DEF_RATING",
        "OPP_PTS",
    }

    # Team stat configurations
    TEAM_STATS = [
        "BASE_PTS",
        "BASE_FG_PCT",
        "BASE_FG3_PCT",
        "BASE_AST",
        "BASE_REB",
        "BASE_STL",
        "BASE_BLK",
        "OPP_PTS",
        "ADV_TM_NET_RATING",
        "ADV_TM_OFF_RATING",
        "ADV_TM_DEF_RATING",
        "MISC_PTS_OFF_TOV",
        "MISC_PTS_2ND_CHANCE",
        "MISC_PTS_FB",
        "MISC_PTS_PAINT",
    ]

    TEAM_STAT_NAMES = {
        "BASE_PTS": "PPG",
        "BASE_FG_PCT": "FG%",
        "BASE_FG3_PCT": "3P%",
        "BASE_AST": "AST",
        "BASE_REB": "REB",
        "BASE_STL": "STL",
        "BASE_BLK": "BLK",
        "ADV_TM_NET_RATING": "Net RTG",
        "ADV_TM_OFF_RATING": "Off RTG",
        "ADV_TM_DEF_RATING": "Def RTG",
        "OPP_PTS": "Opp PPG",
        "MISC_PTS_OFF_TOV": "PTS Off TOV",
        "MISC_PTS_2ND_CHANCE": "PTS 2nd Chance",
        "MISC_PTS_FB": "PTS Fast Break",
        "MISC_PTS_PAINT": "PTS Paint",
    }

    TEAM_STAT_RESPONSE_KEYS = {
        "BASE_PTS": "PTS_PG",
        "BASE_FG_PCT": "FG_PCT",
        "BASE_FG3_PCT": "FG3_PCT",
        "BASE_AST": "AST_PG",
        "BASE_REB": "REB_PG",
        "BASE_STL": "STL_PG",
        "BASE_BLK": "BLK_PG",
        "ADV_TM_NET_RATING": "TM_NET_RATING",
        "ADV_TM_OFF_RATING": "TM_OFF_RATING",
        "ADV_TM_DEF_RATING": "TM_DEF_RATING",
        "OPP_PTS": "OPP_PTS_PG",
        "MISC_PTS_OFF_TOV": "PTS_OFF_TOV_PG",
        "MISC_PTS_2ND_CHANCE": "PTS_2ND_CHANCE_PG",
        "MISC_PTS_FB": "PTS_FB_PG",
        "MISC_PTS_PAINT": "PTS_PAINT_PG",
    }

    # Player stat configurations
    PLAYER_STATS = ["PTS", "AST", "REB", "STL", "BLK", "FG_PCT", "FG3M", "FG3_PCT"]
    PLAYER_STATS_QUERY_TOOL = ["BASE_DD2", "BASE_TD3"]

    PLAYER_STAT_NAMES = {
        "PTS": "PPG",
        "AST": "APG",
        "REB": "RPG",
        "STL": "SPG",
        "BLK": "BPG",
        "FG_PCT": "FG%",
        "FG3M": "3PM",
        "FG3_PCT": "3P%",
        "BASE_DD2": "Double Doubles",
        "BASE_TD3": "Triple Doubles",
    }

    PLAYER_STAT_RESPONSE_KEYS = {
        "PTS": "pts",
        "AST": "ast",
        "REB": "reb",
        "STL": "stl",
        "BLK": "blk",
        "FG_PCT": "fgPct",
        "FG3M": "fg3m",
        "FG3_PCT": "fg3Pct",
        "BASE_DD2": "DD2",
        "BASE_TD3": "TD3",
    }

    def __init__(self):
        """Initialize the NBA client with API keys from environment."""
        self.api_key = os.getenv("NBA_API_KEY")
        self.standings_key = os.getenv("NBA_STANDINGS_KEY")
        self.query_tool_key = os.getenv("QUERY_TOOL_API_KEY")
        self.stats_key = os.getenv("STATS_API_KEY")

        # Cache for standings and rankings (fetched once per run)
        self._standings_cache: dict[int, StandingsData] = {}
        self._team_rankings_cache: dict[str, list[dict]] = {}
        self._player_rankings_cache: dict[str, list[dict]] = {}
        self._injuries_cache: Optional[dict] = None

    def validate_config(self) -> None:
        """Validate required API keys are present."""
        missing = []
        if not self.api_key:
            missing.append("NBA_API_KEY")
        if not self.standings_key:
            missing.append("NBA_STANDINGS_KEY")
        if not self.query_tool_key:
            missing.append("QUERY_TOOL_API_KEY")
        if not self.stats_key:
            missing.append("STATS_API_KEY")

        if missing:
            raise ValueError(f"Missing required API keys: {', '.join(missing)}")

    def get_current_season(self) -> str:
        """Get the current NBA season string (e.g., '2025-26')."""
        now = datetime.now()
        year = now.year
        month = now.month

        if month >= 10:
            return f"{year}-{str(year + 1)[-2:]}"
        else:
            return f"{year - 1}-{str(year)[-2:]}"

    def get_todays_games(self) -> list[GameData]:
        """
        Fetch today's NBA games with all associated data.

        Returns:
            List of GameData objects for today's games
        """
        season = self.get_current_season()
        logger.info(f"Fetching games for season {season}")

        # Fetch schedule
        url = f"{self.NBA_API_BASE}/api/schedule/full"
        headers = {"X-NBA-Api-Key": self.api_key}
        params = {"leagueId": self.LEAGUE_ID, "season": season}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch NBA schedule: {e}")
            raise

        # Extract today's games
        games_raw = self._extract_todays_games(data)
        logger.info(f"Found {len(games_raw)} games for today")

        if not games_raw:
            return []

        # Load standings and rankings (cached)
        self._load_standings(season)
        self._load_rankings(season)
        self._load_injuries()

        # Convert to GameData objects with enriched data
        games = []
        for game_dict in games_raw:
            game = self._build_game_data(game_dict)
            games.append(game)

        return games

    def _extract_todays_games(self, data: dict) -> list[dict]:
        """Extract games list for today from schedule response."""
        if not data or "leagueSchedule" not in data:
            return []

        league_schedule = data["leagueSchedule"]
        if not league_schedule or "gameDates" not in league_schedule:
            return []

        today_str = datetime.now().strftime("%m/%d/%Y")

        for game_date in league_schedule["gameDates"]:
            date_str = game_date.get("gameDate", "")
            if today_str in date_str:
                return game_date.get("games", [])

        return []

    def _format_game_time(self, game_time_est: str) -> tuple[datetime, str]:
        """Convert ISO time to datetime and readable format."""
        try:
            dt = datetime.fromisoformat(game_time_est.replace("Z", "+00:00"))
            time_str = dt.strftime("%I:%M %p ET").lstrip("0")
            return dt, time_str
        except Exception:
            return datetime.now(), "TBD"

    def _load_standings(self, season: str) -> None:
        """Load standings data into cache."""
        if self._standings_cache:
            return

        logger.info("Fetching standings...")
        url = f"{self.NBA_API_BASE}/api/standings/league"
        headers = {"X-NBA-Api-Key": self.standings_key}
        params = {
            "leagueId": self.LEAGUE_ID,
            "season": season,
            "seasonType": "Regular Season",
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            teams = data.get("leagueStandings", {}).get("teams", [])
            all_months = ["oct", "nov", "dec", "jan", "feb", "mar", "apr", "may", "jun"]

            for team in teams:
                team_id = team.get("teamId")
                monthly = {
                    month: team.get(month, "") for month in all_months if team.get(month)
                }

                self._standings_cache[team_id] = StandingsData(
                    team_id=team_id,
                    team_tricode=team.get("teamAbbr", ""),
                    playoff_rank=team.get("playoffRank", 0),
                    streak=team.get("currentStreakText", ""),
                    l10=team.get("l10", ""),
                    home_record=team.get("home", ""),
                    road_record=team.get("road", ""),
                    l10_home=team.get("l10Home", ""),
                    l10_road=team.get("l10Road", ""),
                    monthly_records=monthly,
                )

            logger.info(f"Loaded standings for {len(self._standings_cache)} teams")

        except requests.exceptions.RequestException as e:
            logger.warning(f"Could not fetch standings: {e}")

    def _load_rankings(self, season: str) -> None:
        """Load team and player rankings into cache."""
        if self._team_rankings_cache:
            return

        logger.info("Fetching rankings...")

        # Team rankings
        for stat in self.TEAM_STATS:
            try:
                teams = self._fetch_top_teams_by_stat(stat, season)
                self._team_rankings_cache[stat] = teams
            except Exception as e:
                logger.warning(f"Failed to fetch team stat {stat}: {e}")
                self._team_rankings_cache[stat] = []

        # Player rankings - official leaders
        for stat in self.PLAYER_STATS:
            try:
                players = self._fetch_top_players_by_stat(stat, season)
                self._player_rankings_cache[stat] = players
            except Exception as e:
                logger.warning(f"Failed to fetch player stat {stat}: {e}")
                self._player_rankings_cache[stat] = []

        # Player rankings - query tool (DD2, TD3)
        for stat in self.PLAYER_STATS_QUERY_TOOL:
            try:
                players = self._fetch_query_players_by_stat(stat, season)
                self._player_rankings_cache[stat] = players
            except Exception as e:
                logger.warning(f"Failed to fetch player stat {stat}: {e}")
                self._player_rankings_cache[stat] = []

        logger.info(
            f"Loaded rankings for {len(self._team_rankings_cache)} team stats, "
            f"{len(self._player_rankings_cache)} player stats"
        )

    def _fetch_top_teams_by_stat(self, stat: str, season: str) -> list[dict]:
        """Fetch top 10 teams for a stat."""
        url = f"{self.NBA_API_BASE}/api/querytool/season/team"
        headers = {"X-NBA-Api-Key": self.query_tool_key}

        response_key = self.TEAM_STAT_RESPONSE_KEYS.get(
            stat, stat.split("_", 1)[-1] if "_" in stat else stat
        )
        sort_order = "ASC" if stat in self.TEAM_STATS_ASCENDING else "DESC"

        params = {
            "measures": stat,
            "leagueId": self.LEAGUE_ID,
            "seasonYear": season,
            "seasonType": "Regular Season",
            "perMode": "PerGame",
            "Grouping": "None",
            "sortColumn": f"{response_key}|{sort_order}",
            "MaxRowsReturned": 10,
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        teams = []
        response_stat_key = self.TEAM_STAT_RESPONSE_KEYS.get(stat, stat)

        for rank, team in enumerate(data.get("teams", []), start=1):
            teams.append(
                {
                    "teamId": str(team.get("teamId")),
                    "teamTricode": team.get("teamTricode", ""),
                    "rank": rank,
                    "value": team.get("stats", {}).get(response_stat_key, 0),
                }
            )

        return teams

    def _fetch_top_players_by_stat(self, stat: str, season: str) -> list[dict]:
        """Fetch top 10 players for a stat using official leaders API."""
        url = f"{self.NBA_API_BASE}/api/stats/player/leaders/official"
        headers = {"X-NBA-Api-Key": self.stats_key}

        params = {
            "leagueId": self.LEAGUE_ID,
            "season": season,
            "seasonType": "Regular Season",
            "statCategory": stat,
            "perMode": "PerGame",
            "topX": 10,
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        players = []
        stat_key = self.PLAYER_STAT_RESPONSE_KEYS.get(stat, stat.lower())

        for player in data.get("players", [])[:10]:
            players.append(
                {
                    "playerId": str(player.get("personId", "")),
                    "playerName": player.get("name", ""),
                    "teamTricode": player.get("teamAbbreviation", ""),
                    "rank": player.get("rank", 0),
                    "value": player.get(stat_key, 0),
                }
            )

        return players

    def _fetch_query_players_by_stat(self, stat: str, season: str) -> list[dict]:
        """Fetch top players using query tool API (for totals like DD2, TD3)."""
        url = f"{self.NBA_API_BASE}/api/querytool/season/player"
        headers = {"X-NBA-Api-Key": self.query_tool_key}

        response_key = self.TEAM_STAT_RESPONSE_KEYS.get(
            stat, stat.split("_", 1)[-1] if "_" in stat else stat
        )
        sort_order = "ASC" if stat in self.TEAM_STATS_ASCENDING else "DESC"

        params = {
            "measures": stat,
            "leagueId": self.LEAGUE_ID,
            "seasonYear": season,
            "seasonType": "Regular Season",
            "perMode": "Totals",
            "Grouping": "None",
            "sortColumn": f"{response_key}|{sort_order}",
            "MaxRowsReturned": 10,
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        players = []
        stat_key = self.PLAYER_STAT_RESPONSE_KEYS.get(stat, stat)

        for rank, player in enumerate(data.get("players", [])[:10], start=1):
            players.append(
                {
                    "playerId": str(player.get("playerId", "")),
                    "playerName": player.get("name", ""),
                    "teamTricode": player.get("teamAbbreviation", ""),
                    "rank": rank,
                    "value": player.get("stats", {}).get(stat_key, 0),
                }
            )

        return players

    def _load_injuries(self) -> None:
        """Load injury data into cache."""
        if self._injuries_cache is not None:
            return

        logger.info("Fetching injuries...")
        url = f"{self.NBA_API_BASE}/api/stats/injury"
        headers = {"X-NBA-Api-Key": self.stats_key}
        params = {"leagueId": self.LEAGUE_ID}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            self._injuries_cache = response.json()
            player_count = len(self._injuries_cache.get("players", []))
            logger.info(f"Loaded {player_count} injury records")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Could not fetch injuries: {e}")
            self._injuries_cache = {"players": []}

    def _build_game_data(self, game_dict: dict) -> GameData:
        """Build a GameData object from raw API response."""
        away_team_raw = game_dict.get("awayTeam", {})
        home_team_raw = game_dict.get("homeTeam", {})

        away_team_id = away_team_raw.get("teamId")
        home_team_id = home_team_raw.get("teamId")

        # Get standings data
        away_standings = self._standings_cache.get(away_team_id)
        home_standings = self._standings_cache.get(home_team_id)

        # Build team data
        away_team = TeamData(
            team_id=away_team_id,
            team_tricode=away_team_raw.get("teamTricode", ""),
            team_name=away_team_raw.get("teamName", ""),
            wins=away_team_raw.get("wins", 0),
            losses=away_team_raw.get("losses", 0),
            playoff_rank=away_standings.playoff_rank if away_standings else 0,
            streak=away_standings.streak if away_standings else "",
            l10=away_standings.l10 if away_standings else "",
            home_record=away_standings.home_record if away_standings else "",
            road_record=away_standings.road_record if away_standings else "",
            l10_home=away_standings.l10_home if away_standings else "",
            l10_road=away_standings.l10_road if away_standings else "",
            monthly_records=away_standings.monthly_records if away_standings else {},
        )

        home_team = TeamData(
            team_id=home_team_id,
            team_tricode=home_team_raw.get("teamTricode", ""),
            team_name=home_team_raw.get("teamName", ""),
            wins=home_team_raw.get("wins", 0),
            losses=home_team_raw.get("losses", 0),
            playoff_rank=home_standings.playoff_rank if home_standings else 0,
            streak=home_standings.streak if home_standings else "",
            l10=home_standings.l10 if home_standings else "",
            home_record=home_standings.home_record if home_standings else "",
            road_record=home_standings.road_record if home_standings else "",
            l10_home=home_standings.l10_home if home_standings else "",
            l10_road=home_standings.l10_road if home_standings else "",
            monthly_records=home_standings.monthly_records if home_standings else {},
        )

        # Parse game time
        game_time, game_time_str = self._format_game_time(
            game_dict.get("gameTimeEst", "")
        )

        # Get broadcaster
        broadcaster = None
        broadcasters = game_dict.get("broadcasters", {})
        national = broadcasters.get("nationalBroadcasters", [])
        if national:
            broadcaster = BroadcasterData(
                name=national[0].get("broadcasterDisplay", ""),
                display=national[0].get("broadcasterDisplay", ""),
            )

        # Build game data
        game = GameData(
            game_id=game_dict.get("gameId", ""),
            game_time=game_time,
            game_time_str=game_time_str,
            away_team=away_team,
            home_team=home_team,
            national_broadcaster=broadcaster,
        )

        # Populate rankings
        game.team_rankings = self._get_team_rankings_for_game(away_team, home_team)
        game.player_rankings = self._get_player_rankings_for_game(away_team, home_team)

        # Populate injuries
        game.injuries = self._get_injuries_for_game(away_team_id, home_team_id)

        return game

    def _get_team_rankings_for_game(
        self, away_team: TeamData, home_team: TeamData
    ) -> list[RankingData]:
        """Get all team rankings relevant to a game."""
        rankings = []

        for team in [away_team, home_team]:
            team_id_str = str(team.team_id)

            for stat, teams in self._team_rankings_cache.items():
                for team_data in teams:
                    if team_data["teamId"] == team_id_str:
                        rankings.append(
                            RankingData(
                                name=team.team_tricode,
                                team_tricode=team.team_tricode,
                                stat=self.TEAM_STAT_NAMES.get(stat, stat),
                                rank=team_data["rank"],
                                value=team_data["value"],
                            )
                        )
                        break

        return rankings

    def _get_player_rankings_for_game(
        self, away_team: TeamData, home_team: TeamData
    ) -> list[RankingData]:
        """Get all player rankings relevant to a game."""
        rankings = []
        team_tricodes = {away_team.team_tricode, home_team.team_tricode}

        all_stats = self.PLAYER_STATS + self.PLAYER_STATS_QUERY_TOOL

        for stat in all_stats:
            players = self._player_rankings_cache.get(stat, [])
            for player in players:
                if player["teamTricode"] in team_tricodes and player["rank"] <= 10:
                    rankings.append(
                        RankingData(
                            name=player["playerName"],
                            team_tricode=player["teamTricode"],
                            stat=self.PLAYER_STAT_NAMES.get(stat, stat),
                            rank=player["rank"],
                            value=player["value"],
                        )
                    )

        return rankings

    def _get_injuries_for_game(
        self, away_team_id: int, home_team_id: int
    ) -> list[InjuryData]:
        """Get injuries for both teams in a game."""
        injuries = []

        if not self._injuries_cache:
            return injuries

        for player in self._injuries_cache.get("players", []):
            player_team_id = player.get("teamId")
            if player_team_id in (away_team_id, home_team_id):
                injuries.append(
                    InjuryData(
                        player_name=player.get("playerName", ""),
                        status=player.get("injuryStatus", ""),
                        injury_type=player.get("injuryType", ""),
                        team_tricode=player.get("teamAbbreviation", ""),
                    )
                )

        return injuries
