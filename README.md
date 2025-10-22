# Threads

Automated daily NBA game schedule posted to Slack.


## Current Status

🧪 **Testing** - Currently running `test_slack.py` with mock data that prints a schedule. 

### Active Schedule
Action runs:
- **6:30 PM EDT** 
- **11:15 PM EDT** 

## Production Deployment Checklist

When ready to go live with real NBA data:

### 1. Fix Timezone Schedule (Optional)

Update `.github/workflows/daily_schedule.yml`:
```yaml
on:
  schedule:
    # Remove the 5:30/6:30 PM run - only keep 11 AM
    - cron: '0 15 * * *'   # 11:00 AM EDT (currently active)
    # OR for year-round 11 AM local time:
    - cron: '0 15 * * *'   # 11:00 AM EDT (Mar-Nov)
    - cron: '0 16 * * *'   # 11:00 AM EST (Nov-Mar)
```

### 2. Add NBA API Key to GitHub Secrets

1. Go to: https://github.com/j-ed35/threads/settings/secrets/actions
2. Click **New repository secret**
3. Name: `NBA_API_KEY`
4. Value: Your NBA API key
5. Click **Add secret**

### 3. Update Workflow to Use Real API

Edit `.github/workflows/daily_schedule.yml`:
```yaml
- name: Run threads
  env:
    NBA_API_KEY: ${{ secrets.NBA_API_KEY }}
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
  run: python main.py  # Changed from test_slack.py
```

### 4. Test Real API Locally First

Before deploying:
```bash
# Make sure .env has NBA_API_KEY set
python main.py
```

Verify the output format looks correct in Slack.

### 5. Update and Deploy
```bash
git add .github/workflows/daily_schedule.yml
git commit -m "Switch to production NBA API"
git push
```

### 6. Manual Test on GitHub

1. Go to Actions tab
2. Click **Daily NBA Schedule**
3. Click **Run workflow**
4. Verify real games appear in Slack

## Future Enhancements

- [ ] Add team records (W-L)
- [ ] Add player leaders (PPG, APG, RPG, 3PM, FG% leaders)
- [ ] Add injury reports
- [ ] Handle days with no games (off days, all-star break)


### Updating Game Format

Edit `src/formatter.py` to change how games are displayed.
- Will need to add the slack threads for each game 

### Changing Slack Message Format

Edit `src/slack_client.py` in the `send_games()` method.

### Slack emohi updates

Edit: :_den:, :cle-: and :tor-: all have different logo names

### Adding New Data Sources

1. Create new client in `src/` (e.g., `src/injuries_api.py`)
2. Update `main.py` to fetch and combine data
3. Update `src/formatter.py` to include new data in output

## Troubleshooting

### Workflow runs but no Slack message
- Check GitHub Actions logs for errors
- Verify `SLACK_WEBHOOK_URL` secret is set correctly
- Test locally with `python test_slack.py`

### Wrong game times displayed
- Check timezone handling in `src/formatter.py`
- NBA API returns times in UTC(?)

### Workflow doesn't run on schedule
- GitHub Actions can be delayed up to 10 minutes during high load
- Verify cron syntax at https://crontab.guru/
- Check if repository has Actions enabled

### Project Structure
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