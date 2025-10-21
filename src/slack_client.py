import requests
from datetime import date
from .config import Config

today = date.today()

# Example 2: DD/MM/YYYY format
date_string = today.strftime("%m/%d/%Y")


def slack_group(webhook_url):
    """Determine which slack group is being used based on webhook URL"""
    if webhook_url == Config.SLACK_WEBHOOK_URL:
        return "#qa-fb-social-alerts"
    elif webhook_url == Config.ED_TEST_WEBHOOK_URL:
        return "#ed-testing"
    else:
        return "#unknown-channel"


class SlackClient:
    def __init__(self):
        self.webhook_url = Config.SLACK_WEBHOOK_URL

    def send_message(self, text):
        """Send a message to Slack"""
        payload = {"text": text}

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            channel = slack_group(self.webhook_url)
            return f"✓ Message sent! Check {channel}"
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to send Slack message: {e}")

    def send_games(self, games_text):
        """Send formatted games to Slack"""
        if not games_text:
            message = "No NBA games scheduled for today"
        else:
            message = f"**TEST** *NBA Games - {date_string}*\n\n{games_text}"

        return self.send_message(message)
