"""
Slack Web API client for threads_v2.

Uses Slack Web API with bot token (chat:write scope) instead of webhooks.
Supports posting parent messages and threaded replies.
"""

import os
import json
import requests
from typing import Optional

from ..util.logging import get_logger

logger = get_logger("threads_v2.slack")


class SlackAPIError(Exception):
    """Raised when Slack API returns an error."""

    def __init__(self, error: str, response: dict):
        self.error = error
        self.response = response
        super().__init__(f"Slack API error: {error}")


class SlackClientV2:
    """
    Slack Web API client.

    Uses bot token authentication and supports:
    - Posting messages to channels
    - Posting threaded replies
    - Block Kit formatting with plain text fallback
    """

    SLACK_API_BASE = "https://slack.com/api"

    # Channel aliases for convenience
    CHANNEL_ALIASES = {
        "ed_testing": "SLACK_CHANNEL_ID_ED_TESTING",
        "mookie": "SLACK_CHANNEL_ID_MOOKIE",
        "daily_threads": "SLACK_CHANNEL_ID_DAILY_THREADS",
    }

    def __init__(self, bot_token: Optional[str] = None):
        """
        Initialize Slack client.

        Args:
            bot_token: Slack bot token (xoxb-...). If not provided, reads from
                      SLACK_BOT_TOKEN environment variable.
        """
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")

        if not self.bot_token:
            raise ValueError(
                "SLACK_BOT_TOKEN not found. Set it in .env or pass to constructor."
            )

        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json; charset=utf-8",
            }
        )

    def get_channel_id(self, channel_alias: str) -> str:
        """
        Get channel ID from alias or environment variable.

        Args:
            channel_alias: Either a channel alias (e.g., "ed_testing") or
                          an environment variable name, or a raw channel ID.

        Returns:
            The channel ID string.

        Raises:
            ValueError: If channel ID cannot be resolved.
        """
        # Check if it's a known alias
        if channel_alias in self.CHANNEL_ALIASES:
            env_var = self.CHANNEL_ALIASES[channel_alias]
            channel_id = os.getenv(env_var)
            if not channel_id:
                raise ValueError(
                    f"Channel alias '{channel_alias}' requires {env_var} to be set"
                )
            return channel_id

        # Check if it's an environment variable name
        if channel_alias.startswith("SLACK_CHANNEL_ID_"):
            channel_id = os.getenv(channel_alias)
            if not channel_id:
                raise ValueError(f"Environment variable {channel_alias} not set")
            return channel_id

        # Check if it looks like a raw channel ID (starts with C, D, or G)
        if channel_alias.startswith(("C", "D", "G")) and len(channel_alias) >= 9:
            return channel_alias

        # Try treating it as an env var without prefix
        env_var = f"SLACK_CHANNEL_ID_{channel_alias.upper()}"
        channel_id = os.getenv(env_var)
        if channel_id:
            return channel_id

        raise ValueError(
            f"Could not resolve channel: '{channel_alias}'. "
            f"Use an alias ({', '.join(self.CHANNEL_ALIASES.keys())}), "
            f"an env var name, or a raw channel ID."
        )

    def post_message(
        self,
        channel_id: str,
        text: str,
        blocks: Optional[list[dict]] = None,
        thread_ts: Optional[str] = None,
    ) -> str:
        """
        Post a message to a Slack channel.

        Args:
            channel_id: Channel ID to post to
            text: Plain text message (used as fallback if blocks provided)
            blocks: Optional Block Kit blocks for rich formatting
            thread_ts: Optional thread timestamp to reply to

        Returns:
            The message timestamp (ts) for threading

        Raises:
            SlackAPIError: If Slack returns ok=false
        """
        url = f"{self.SLACK_API_BASE}/chat.postMessage"

        payload = {
            "channel": channel_id,
            "text": text,
        }

        if blocks:
            payload["blocks"] = blocks

        if thread_ts:
            payload["thread_ts"] = thread_ts

        try:
            response = self._session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                error = data.get("error", "unknown_error")
                logger.error(f"Slack API error: {error}")
                logger.error(f"Full response: {json.dumps(data, indent=2)}")
                raise SlackAPIError(error, data)

            ts = data.get("ts")
            logger.info(f"Posted message to {channel_id}, ts={ts}")
            return ts

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error posting to Slack: {e}")
            raise

    def post_thread_reply(
        self,
        channel_id: str,
        thread_ts: str,
        text: str,
        blocks: Optional[list[dict]] = None,
    ) -> str:
        """
        Post a threaded reply to an existing message.

        Args:
            channel_id: Channel ID
            thread_ts: Timestamp of parent message to reply to
            text: Plain text message
            blocks: Optional Block Kit blocks

        Returns:
            The reply message timestamp (ts)
        """
        return self.post_message(
            channel_id=channel_id,
            text=text,
            blocks=blocks,
            thread_ts=thread_ts,
        )

    def post_game_with_thread(
        self,
        channel_id: str,
        parent_text: str,
        thread_text: str,
        parent_blocks: Optional[list[dict]] = None,
        thread_blocks: Optional[list[dict]] = None,
    ) -> tuple[str, str]:
        """
        Post a parent message and threaded reply for a game.

        This is a convenience method that posts both messages in sequence.

        Args:
            channel_id: Channel ID to post to
            parent_text: Text for parent message
            thread_text: Text for threaded reply
            parent_blocks: Optional blocks for parent
            thread_blocks: Optional blocks for thread

        Returns:
            Tuple of (parent_ts, thread_ts)
        """
        # Post parent message
        parent_ts = self.post_message(
            channel_id=channel_id,
            text=parent_text,
            blocks=parent_blocks,
        )

        # Post threaded reply
        thread_ts = self.post_thread_reply(
            channel_id=channel_id,
            thread_ts=parent_ts,
            text=thread_text,
            blocks=thread_blocks,
        )

        return parent_ts, thread_ts

    def test_connection(self) -> dict:
        """
        Test the Slack connection using auth.test.

        Returns:
            Response data including team and bot info

        Raises:
            SlackAPIError: If authentication fails
        """
        url = f"{self.SLACK_API_BASE}/auth.test"

        try:
            response = self._session.post(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                error = data.get("error", "unknown_error")
                raise SlackAPIError(error, data)

            logger.info(
                f"Connected to Slack workspace: {data.get('team')} as {data.get('user')}"
            )
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error testing Slack connection: {e}")
            raise
