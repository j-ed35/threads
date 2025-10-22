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
        mock_games = """
    CLE (0-0) :CLE-: at NYK (0-0) :NYK: | 7:00 PM ET
    :reminder_ribbon: REMINDER
    :t20: MILESTONES
    :GTD: GTD/QUESTIONABLE
    :out: INJURIES
    SAS (0-0) :SAS: at DAL (0-0) :DAL: | 9:30 PM ET
    :reminder_ribbon: REMINDER
    :t20: MILESTONES
    :GTD: GTD/QUESTIONABLE
    :out: INJURIES
    BKN (0-0) :BKN: at CHA (0-0) :CHA: | 7:00 PM ET
    :reminder_ribbon: REMINDER
    :t20: MILESTONES
    :GTD: GTD/QUESTIONABLE
    :out: INJURIES
    MIA (0-0) :MIA: at ORL (0-0) :ORL: | 7:00 PM ET
    :reminder_ribbon: REMINDER
    :t20: MILESTONES
    :GTD: GTD/QUESTIONABLE
    :out: INJURIES
    TOR (0-0) :TOR-: at ATL (0-0) :ATL: | 7:30 PM ET
    :reminder_ribbon: REMINDER
    :t20: MILESTONES
    :GTD: GTD/QUESTIONABLE
    :out: INJURIES
    PHI (0-0) :PHI: at BOS (0-0) :BOS: | 7:30 PM ET
    :reminder_ribbon: REMINDER
    :t20: MILESTONES
    :GTD: GTD/QUESTIONABLE
    :out: INJURIES
    DET (0-0) :DET: at CHI (0-0) :CHI: | 8:00 PM ET
    :reminder_ribbon: REMINDER
    :t20: MILESTONES
    :GTD: GTD/QUESTIONABLE
    :out: INJURIES
    NOP (0-0) :NOP: at MEM (0-0) :MEM: | 8:00 PM ET
    :reminder_ribbon: REMINDER
    :t20: MILESTONES
    :GTD: GTD/QUESTIONABLE
    :out: INJURIES
    WAS (0-0) :WAS: at MIL (0-0) :MIL: | 8:00 PM ET
    :reminder_ribbon: REMINDER
    :t20: MILESTONES
    :GTD: GTD/QUESTIONABLE
    :out: INJURIES
    LAC (0-0) :LAC: at UTA (0-0) :UTA: | 9:00 PM ET
    :reminder_ribbon: REMINDER
    :t20: MILESTONES
    :GTD: GTD/QUESTIONABLE
    :out: INJURIES
    SAC (0-0) :SAC: at PHX (0-0) :PHX: | 10:00 PM ET
    :reminder_ribbon: REMINDER
    :t20: MILESTONES
    :GTD: GTD/QUESTIONABLE
    :out: INJURIES
    MIN (0-0) :MIN: at POR (0-0) :POR: | 10:00 PM ET
    :reminder_ribbon: REMINDER
    :t20: MILESTONES
    :GTD: GTD/QUESTIONABLE
    :out: INJURIES"""

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
