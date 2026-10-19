import time

import requests

from .config import Config


class SlackClient:
    """Posts to one Slack channel via chat.postMessage."""

    URL = "https://slack.com/api/chat.postMessage"

    def __init__(self, channel_id: str):
        self.channel_id = channel_id
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {Config.SLACK_BOT_TOKEN}"

    def send_message(self, text: str, thread_ts: str = None) -> dict:
        payload = {"channel": self.channel_id, "text": text}
        if thread_ts:
            payload["thread_ts"] = thread_ts
        # chat.postMessage allows ~1 message/second per channel; wait out 429s.
        for _ in range(5):
            response = self.session.post(self.URL, json=payload, timeout=10)
            if response.status_code != 429:
                break
            time.sleep(int(response.headers.get("Retry-After", 1)))
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise Exception(f"Slack API error: {data.get('error', 'unknown error')}")
        return data

    def send_game_with_thread(
        self, parent_text: str, thread_text: str = None, injury_thread: str = None
    ) -> dict:
        """Post the parent message, then each non-empty reply in its thread."""
        ts = self.send_message(parent_text).get("ts")
        for reply in (thread_text, injury_thread):
            if reply and ts:
                self.send_message(reply, thread_ts=ts)
        return {"ts": ts}
