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
        mock_games = """Cleveland Cavaliers (0-0) :CLE-: at New York Knicks (0-0) :NYK: | 7:00 PM ET
                - :reminder_ribbon: REMINDER
                - :GTD: GTD/QUESTIONABLE
                - :out: INJURIES
        San Antonio Spurs (0-0) :SAS: at Dallas Mavericks (0-0) :DAL: | 9:30 PM ET
                - :reminder_ribbon: REMINDER
                - :GTD: GTD/QUESTIONABLE
                - :out: INJURIES
        Brooklyn Nets (0-0) :BKN: at Charlotte Hornets (0-0) :CHA: | 7:00 PM ET
                - :reminder_ribbon: REMINDER
                - :GTD: GTD/QUESTIONABLE
                - :out: INJURIES
        Miami Heat (0-0) :MIA: at Orlando Magic (0-0) :ORL: | 7:00 PM ET
                - :reminder_ribbon: REMINDER
                - :GTD: GTD/QUESTIONABLE
                - :out: INJURIES
        Toronto Raptors (0-0) :TOR-: at Atlanta Hawks (0-0) :ATL: | 7:30 PM ET
                - :reminder_ribbon: REMINDER
                - :GTD: GTD/QUESTIONABLE
                - :out: INJURIES
        Philadelphia 76ers (0-0) :PHI: at Boston Celtics (0-0) :BOS: | 7:30 PM ET
                - :reminder_ribbon: REMINDER
                - :GTD: GTD/QUESTIONABLE
                - :out: INJURIES
        Detroit Pistons (0-0) :DET: at Chicago Bulls (0-0) :CHI: | 8:00 PM ET
                - :reminder_ribbon: REMINDER
                - :GTD: GTD/QUESTIONABLE
                - :out: INJURIES
        New Orleans Pelicans (0-0) :NOP: at Memphis Grizzlies (0-0) :MEM: | 8:00 PM ET
                - :reminder_ribbon: REMINDER
                - :GTD: GTD/QUESTIONABLE
                - :out: INJURIES
        Washington Wizards (0-0) :WAS: at Milwaukee Bucks (0-0) :MIL: | 8:00 PM ET
                - :reminder_ribbon: REMINDER
                - :GTD: GTD/QUESTIONABLE
                - :out: INJURIES
        LA Clippers (0-0) :LAC: at Utah Jazz (0-0) :UTA: | 9:00 PM ET
                - :reminder_ribbon: REMINDER
                - :GTD: GTD/QUESTIONABLE
                - :out: INJURIES
        Sacramento Kings (0-0) :SAC: at Phoenix Suns (0-0) :PHX: | 10:00 PM ET
                - :reminder_ribbon: REMINDER
                - :GTD: GTD/QUESTIONABLE
                - :out: INJURIES
        Minnesota Timberwolves (0-0) :MIN: at Portland Trail Blazers (0-0) :POR: | 10:00 PM ET
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
