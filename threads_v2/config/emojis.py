"""
Centralized emoji configuration for threads_v2.

All emojis used in Slack messages are defined here for easy maintenance.
"""

import json
from pathlib import Path

# Load emojis from JSON file
_EMOJIS_FILE = Path(__file__).parent / "emojis.json"

with open(_EMOJIS_FILE, "r") as f:
    EMOJIS = json.load(f)


def get_team_emoji(team_tricode: str) -> str:
    """
    Get Slack emoji for a team.

    Args:
        team_tricode: Three-letter team code (e.g., "LAL", "BOS")

    Returns:
        Formatted Slack emoji string (e.g., ":_lal:")
    """
    tricode_upper = team_tricode.upper()
    emoji_name = EMOJIS["teams"].get(tricode_upper, f"_{tricode_upper.lower()}")
    return f":{emoji_name}:"


def get_broadcaster_emoji(broadcaster_name: str) -> str:
    """
    Get Slack emoji for a broadcaster.

    Args:
        broadcaster_name: Display name of broadcaster (e.g., "ESPN", "TNT")

    Returns:
        Formatted Slack emoji string (e.g., ":_ESPN:")
    """
    emoji_name = EMOJIS["broadcasters"].get(
        broadcaster_name, f"_{broadcaster_name.replace(' ', '')}"
    )
    return f":{emoji_name}:"


def get_section_emoji(section: str) -> str:
    """
    Get Slack emoji for a section header.

    Args:
        section: Section identifier (e.g., "top10", "notable", "gtd")

    Returns:
        Formatted Slack emoji string (e.g., ":t10:")
    """
    emoji_name = EMOJIS["sections"].get(section, section)
    return f":{emoji_name}:"
