import requests
from datetime import date
from .config import Config


class SlackClient:
    """Slack client using OAuth and chat.postMessage API."""

    SLACK_API_URL = "https://slack.com/api"

    def __init__(self, channel_id: str = None):
        """
        Initialize Slack client with OAuth.

        Args:
            channel_id: Slack channel ID to post to.
                       Defaults to SLACK_CHANNEL_ID_DAILY_THREADS.
        """
        self.token = Config.SLACK_BOT_TOKEN
        # Default to the daily threads channel
        self.channel_id = channel_id or Config.SLACK_CHANNEL_ID_DAILY_THREADS
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def send_message(self, text: str, thread_ts: str = None) -> dict:
        """
        Send a message to Slack using chat.postMessage.

        Args:
            text: Message text (supports Slack markdown)
            thread_ts: Optional thread timestamp to reply to

        Returns:
            Dict with 'ok', 'ts' (timestamp), and other response data
        """
        url = f"{self.SLACK_API_URL}/chat.postMessage"

        payload = {
            "channel": self.channel_id,
            "text": text,
        }

        if thread_ts:
            payload["thread_ts"] = thread_ts

        try:
            response = requests.post(
                url, headers=self.headers, json=payload, timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                error = data.get("error", "Unknown error")
                raise Exception(f"Slack API error: {error}")

            return data

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to send Slack message: {e}")

    def send_game_with_thread(
        self, parent_text: str, thread_text: str = None
    ) -> dict:
        """
        Send a game message with an optional threaded reply.

        Args:
            parent_text: Main message text for the parent message
            thread_text: Optional text for the threaded reply

        Returns:
            Dict with parent message response and optional thread response
        """
        # Send parent message
        parent_response = self.send_message(parent_text)
        parent_ts = parent_response.get("ts")

        result = {
            "parent": parent_response,
            "thread": None,
        }

        # Send thread reply if provided
        if thread_text and parent_ts:
            thread_response = self.send_message(thread_text, thread_ts=parent_ts)
            result["thread"] = thread_response

        return result

    def send_games(self, games_text: str) -> str:
        """
        Send formatted games to Slack (legacy method for compatibility).

        Args:
            games_text: Formatted games text

        Returns:
            Success message string
        """
        today = date.today()
        date_string = today.strftime("%m/%d/%Y")

        if not games_text:
            message = "No NBA games scheduled for today"
        else:
            message = f"*NBA Games - {date_string}*\n\n{games_text}"

        self.send_message(message)
        return f"✓ Message sent to channel {self.channel_id}"
