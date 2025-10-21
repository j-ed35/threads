from src.slack_client import SlackClient
from src.config import Config


def test_slack():
    try:
        print("Validating config...")
        Config.validate(require_nba_key=False)  # Don't require NBA key for testing
        print("✓ Config validated")

        print(f"Webhook URL starts with: {Config.SLACK_WEBHOOK_URL[:30]}...")

        slack = SlackClient()

        # Mock game data
        mock_games = """Houston Rockets :HOU: at Oklahoma City Thunder :OKC: | 7:30 PM ET
        - :reminder_ribbon: REMINDER
        - :GTD: GTD/QUESTIONABLE
        - :out: INJURIES
Golden State Warriors :GSW: at Los Angeles Lakers :LAL: | 10:00 PM ET
        - :reminder_ribbon: REMINDER
        - :GTD: GTD/QUESTIONABLE
        - :out: INJURIES"""

        print("Sending test message to Slack...")
        result = slack.send_games(mock_games)
        print(f"✓ Message sent successfully: {result}")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    test_slack()
