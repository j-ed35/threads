"""
Block Kit builder for threads_v2.

Builds Slack Block Kit payloads for rich formatting.
Falls back to plain text if blocks are not needed or fail validation.
"""

from typing import Optional


def build_blocks_for_message(text: str) -> Optional[list[dict]]:
    """
    Build Block Kit blocks from plain text message.

    For Phase 1, we use simple section blocks with mrkdwn text.
    This preserves emoji formatting and bold text.

    Args:
        text: Plain text message with Slack mrkdwn formatting

    Returns:
        List of Block Kit block dictionaries, or None to use plain text only
    """
    # Split text into sections (double newline = new block)
    paragraphs = text.split("\n\n")

    blocks = []

    for paragraph in paragraphs:
        if not paragraph.strip():
            continue

        # Each paragraph becomes a section block
        block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": paragraph.strip(),
            },
        }
        blocks.append(block)

    # Add divider at end
    blocks.append({"type": "divider"})

    return blocks if blocks else None


def build_header_block(text: str) -> dict:
    """Build a header block."""
    return {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": text[:150],  # Header max length is 150
            "emoji": True,
        },
    }


def build_section_block(text: str) -> dict:
    """Build a section block with mrkdwn."""
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": text[:3000],  # Section text max length is 3000
        },
    }


def build_context_block(elements: list[str]) -> dict:
    """Build a context block with multiple mrkdwn elements."""
    return {
        "type": "context",
        "elements": [
            {"type": "mrkdwn", "text": elem[:2000]} for elem in elements[:10]  # Max 10 elements
        ],
    }


def build_divider_block() -> dict:
    """Build a divider block."""
    return {"type": "divider"}


def build_game_blocks(
    header: str,
    standings_lines: list[str],
    rankings_lines: list[str],
    injury_lines: list[str],
) -> list[dict]:
    """
    Build comprehensive blocks for a game message.

    Args:
        header: Game header text (matchup, time, etc.)
        standings_lines: List of standings lines
        rankings_lines: List of rankings lines
        injury_lines: List of injury lines

    Returns:
        List of Block Kit blocks
    """
    blocks = []

    # Header
    blocks.append(build_section_block(header))

    # Standings
    if standings_lines:
        blocks.append(build_section_block("\n".join(standings_lines)))

    # Rankings
    if rankings_lines:
        # Group rankings into reasonable chunks
        chunk_size = 5
        for i in range(0, len(rankings_lines), chunk_size):
            chunk = rankings_lines[i : i + chunk_size]
            blocks.append(build_section_block("\n".join(chunk)))

    # Injuries
    if injury_lines:
        blocks.append(build_section_block("\n".join(injury_lines)))

    # Divider at end
    blocks.append(build_divider_block())

    return blocks
