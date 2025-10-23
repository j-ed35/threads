# Threads

## Overview

Automated daily NBA game schedule posted to Slack with threaded discussions for each game.

## Configuration

Update `.github/workflows/daily_schedule.yml` for scheduling:
```yaml
on:
  schedule:
    - cron: '0 15 * * *'   # 11:00 AM EDT
```

## Features

- Daily NBA game schedules posted to Slack
- Individual threads created for each game
- Automated GitHub Actions workflow

## Future Enhancements

- [ ] Add team records (W-L)
- [ ] Add player leaders (PPG, APG, RPG, 3PM, FG% leaders)
- [ ] Add injury reports
- [ ] Handle days with no games (off days, all-star break)

## Development

### Updating Game Format
Edit `src/formatter.py` to change how games are displayed.

### Changing Slack Message Format
Edit `src/slack_client.py` in the `send_games()` method.

## Troubleshooting

### Workflow runs but no Slack message
- Check GitHub Actions logs for errors
- Verify `SLACK_WEBHOOK_URL` secret is set correctly
- Test locally with `python test_slack.py`

### Wrong game times displayed
- Check timezone handling in `src/formatter.py`
- NBA API returns times in UTC

### Workflow doesn't run on schedule
- GitHub Actions can be delayed up to 10 minutes during high load
- Verify cron syntax at https://crontab.guru/
- Check if repository has Actions enabled

## Project Structure
```
threads/
├── .github/workflows/      # GitHub Actions automation
├── src/                    # Source code
│   ├── config.py          # Configuration management
│   ├── nba_api.py         # NBA API client
│   ├── formatter.py       # Data formatting
│   └── slack_client.py    # Slack integration
├── main.py                # Production entry point
└── test_slack.py          # Test script with mock data
```