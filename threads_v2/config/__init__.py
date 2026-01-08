"""
Configuration module for threads_v2.

Contains centralized emoji mappings, text labels, and section headers.
"""

from .emojis import get_team_emoji, get_broadcaster_emoji, EMOJIS
from .labels import LABELS, SECTION_HEADERS

__all__ = [
    "get_team_emoji",
    "get_broadcaster_emoji",
    "EMOJIS",
    "LABELS",
    "SECTION_HEADERS",
]
