"""
Injuries module for fetching and formatting NBA injury data.
"""

import requests
import os
from datetime import datetime
from typing import Dict, List

from .mapping import PLAYERS_EXCLUDED


class InjuriesClient:
    """Client for fetching NBA injury data from the Stats API"""

    # Class-level cache to persist across instances
    _shared_injury_cache = None

    def __init__(self):
        self.base_url = "https://api.nba.com/v0/api/stats/injury"
        self.api_key = os.getenv("STATS_API_KEY")

        if not self.api_key:
            raise ValueError("STATS_API_KEY not found in environment")

    def get_all_injuries(self, league_id: str = "00") -> Dict:
        """
        Fetch all current injuries for the league (with caching).

        Args:
            league_id: Two digit league ID (default "00" for NBA)

        Returns:
            Dictionary containing injury data
        """
        # Return cached data if available (class-level cache)
        if InjuriesClient._shared_injury_cache is not None:
            return InjuriesClient._shared_injury_cache

        headers = {
            "X-NBA-Api-Key": self.api_key,  # Changed from 'Authorization': 'Bearer ...'
            "Accept": "application/json",
        }

        params = {"leagueId": league_id}

        try:
            response = requests.get(
                self.base_url, headers=headers, params=params, timeout=10
            )
            response.raise_for_status()
            InjuriesClient._shared_injury_cache = response.json()
            return InjuriesClient._shared_injury_cache

        except requests.exceptions.RequestException as e:
            print(f"Error fetching injury data: {e}")
            return {"leagueId": league_id, "players": []}

    def get_injuries_by_team(self, team_id: int) -> Dict[str, List[str]]:
        """
        Get injuries for a specific team, grouped by status.

        Args:
            team_id: NBA team ID

        Returns:
            Dictionary with 'GTD' and 'OUT' keys containing lists of player names
        """
        all_injuries = self.get_all_injuries()

        if not all_injuries or "players" not in all_injuries:
            return {"GTD": [], "OUT": []}

        gtd_players = []
        out_players = []

        for player in all_injuries["players"]:
            if player.get("teamId") == team_id:
                player_name = player.get("playerName", "")
                # Skip excluded players
                if player_name in PLAYERS_EXCLUDED:
                    continue
                injury_status = player.get("injuryStatus", "").upper()

                if injury_status in ["GTD", "QUESTIONABLE", "DOUBTFUL"]:
                    gtd_players.append(player_name)
                elif injury_status in ["OUT"]:
                    out_players.append(player_name)

        return {"GTD": gtd_players, "OUT": out_players}

    def get_detailed_injuries_by_team(self, team_id: int) -> List[Dict]:
        """
        Get detailed injury information for a specific team.

        Args:
            team_id: NBA team ID

        Returns:
            List of dictionaries with detailed player injury info
        """
        all_injuries = self.get_all_injuries()

        if not all_injuries or "players" not in all_injuries:
            return []

        team_injuries = []

        for player in all_injuries["players"]:
            if player.get("teamId") == team_id:
                player_name = player.get("playerName", "")
                # Skip excluded players
                if player_name in PLAYERS_EXCLUDED:
                    continue
                injury_info = {
                    "playerName": player_name,
                    "injuryStatus": player.get("injuryStatus", ""),
                    "injuryType": player.get("injuryType", ""),
                    "injuryLocation": player.get("injuryLocation", ""),
                    "injuryDetails": player.get("injuryDetails", ""),
                    "teamAbbreviation": player.get("teamAbbreviation", ""),
                }
                team_injuries.append(injury_info)

        return team_injuries

    def format_game_injuries(self, home_team_id: int, away_team_id: int) -> str:
        """
        Format injuries for both teams in a game (compact format).
        Away team players first, then pipe separator, then home team players.

        Args:
            home_team_id: Home team ID
            away_team_id: Away team ID

        Returns:
            Formatted injury string with GTD and OUT sections
        """
        away_injuries = self.get_injuries_by_team(away_team_id)
        home_injuries = self.get_injuries_by_team(home_team_id)

        lines = []

        # GTD/QUESTIONABLE section - away first, then pipe, then home
        away_gtd = away_injuries["GTD"]
        home_gtd = home_injuries["GTD"]
        if away_gtd or home_gtd:
            gtd_parts = []
            if away_gtd:
                gtd_parts.append(", ".join(away_gtd))
            if home_gtd:
                gtd_parts.append(", ".join(home_gtd))
            gtd_names = (
                " | ".join(gtd_parts)
                if len(gtd_parts) > 1
                else gtd_parts[0]
                if gtd_parts
                else ""
            )
            lines.append(f":gtd: {gtd_names}")

        # OUT section - away first, then pipe, then home
        away_out = away_injuries["OUT"]
        home_out = home_injuries["OUT"]
        if away_out or home_out:
            out_parts = []
            if away_out:
                out_parts.append(", ".join(away_out))
            if home_out:
                out_parts.append(", ".join(home_out))
            out_names = (
                " | ".join(out_parts)
                if len(out_parts) > 1
                else out_parts[0]
                if out_parts
                else ""
            )
            lines.append(f":out: {out_names}")

        return "\n".join(lines)

    def format_game_injury_thread(
        self, home_team_id: int, away_team_id: int, home_tricode: str, away_tricode: str
    ) -> str:
        """
        Format detailed injury report for a single game as a thread message.

        Args:
            home_team_id: Home team ID
            away_team_id: Away team ID
            home_tricode: Home team tricode (e.g., "OKC")
            away_tricode: Away team tricode (e.g., "TOR")

        Returns:
            Formatted detailed injury thread string
        """
        away_injuries = (
            self.get_detailed_injuries_by_team(away_team_id) if away_team_id else []
        )
        home_injuries = (
            self.get_detailed_injuries_by_team(home_team_id) if home_team_id else []
        )

        if not away_injuries and not home_injuries:
            return ""

        # Hardcode current time as github actions runs just after 12pm ET
        # current_time = datetime.now().strftime("%I%p").lstrip("0")
        current_time = "12PM"
        lines = [f"_Injuries Current as of {current_time} ET_", ""]

        # Separate into GTD/Questionable and OUT
        gtd_injuries = []
        out_injuries = []

        for injury in away_injuries:
            injury["tricode"] = away_tricode
            status = injury["injuryStatus"].upper()
            if status in ["GTD", "QUESTIONABLE", "DOUBTFUL"]:
                gtd_injuries.append(injury)
            elif status == "OUT":
                out_injuries.append(injury)

        for injury in home_injuries:
            injury["tricode"] = home_tricode
            status = injury["injuryStatus"].upper()
            if status in ["GTD", "QUESTIONABLE", "DOUBTFUL"]:
                gtd_injuries.append(injury)
            elif status == "OUT":
                out_injuries.append(injury)

        # GTD/QUESTIONABLE section
        if gtd_injuries:
            lines.append(":gtd: *GTD/QUESTIONABLE*")
            for injury in gtd_injuries:
                tricode = injury["tricode"]
                player_name = injury["playerName"]
                injury_type = injury["injuryType"]
                injury_status = injury["injuryStatus"]
                lines.append(
                    f":_{tricode.lower()}: {player_name} - {injury_type} ({injury_status})"
                )
            lines.append("")

        # OUT section
        if out_injuries:
            lines.append(":out: *OUT*")
            for injury in out_injuries:
                tricode = injury["tricode"]
                player_name = injury["playerName"]
                injury_type = injury["injuryType"]
                injury_status = injury["injuryStatus"]
                lines.append(
                    f":_{tricode.lower()}: {player_name} - {injury_type} ({injury_status})"
                )

        return "\n".join(lines)

    def format_full_injury_report(self, games: List[Dict]) -> str:
        """
        Format a detailed injury report for all games in a compact format.

        Args:
            games: List of game dictionaries with team info

        Returns:
            Formatted detailed injury report string
        """
        report_lines = ["━━━━━━━━━━━━━━━━━━━━━━", "*Full Injury Report*"]

        for game in games:
            away_team = game.get("awayTeam", {})
            home_team = game.get("homeTeam", {})

            away_team_id = away_team.get("teamId")
            home_team_id = home_team.get("teamId")
            away_tricode = away_team.get("teamTricode", "")
            home_tricode = home_team.get("teamTricode", "")

            # Get detailed injuries for both teams
            away_injuries = (
                self.get_detailed_injuries_by_team(away_team_id) if away_team_id else []
            )
            home_injuries = (
                self.get_detailed_injuries_by_team(home_team_id) if home_team_id else []
            )

            # Only add section if there are injuries
            if away_injuries or home_injuries:
                game_header = f"\n{away_tricode} :_{away_tricode.lower()}: @ {home_tricode} :_{home_tricode.lower()}:"
                report_lines.append(game_header)

                # Combine both teams' injuries into one list
                all_injuries = []

                # Away team injuries
                for injury in away_injuries:
                    player_name = injury["playerName"]
                    injury_type = injury["injuryType"]
                    injury_status = injury["injuryStatus"]
                    all_injuries.append(
                        f":_{away_tricode.lower()}: {player_name} - {injury_type} ({injury_status})"
                    )

                # Home team injuries
                for injury in home_injuries:
                    player_name = injury["playerName"]
                    injury_type = injury["injuryType"]
                    injury_status = injury["injuryStatus"]
                    all_injuries.append(
                        f":_{home_tricode.lower()}: {player_name} - {injury_type} ({injury_status})"
                    )

                # Add all injuries for this game
                report_lines.extend(all_injuries)

        # If no injuries at all, return empty string
        if len(report_lines) <= 2:
            return ""

        return "\n".join(report_lines)
