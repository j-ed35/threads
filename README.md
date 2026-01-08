# Threads

Automated NBA game information system that fetches daily schedules, team/player statistics, and posts formatted game previews to Slack.

## Core Features

- Daily NBA game schedules with team records, broadcast info, and game times
- Team statistics: streaks, L10, top-10 rankings (PPG, FG%, 3P%, AST, REB, etc.)
- Player statistics: top-10 league rankings for relevant players
- Automated via GitHub Actions (runs daily)
- Creates individual message threads per game

## Project Structure

```
threads/
├── src/                   # Core application code
│   ├── nba_api.py        # API client for fetching game/stats data
│   ├── rankings.py       # Team/player rankings processing
│   ├── formatter.py      # Formats game data for display
│   ├── slack_client.py   # Slack message posting
│   └── config.py         # Config management (env vars)
├── personal/             # Extended analytics scripts
│   ├── monthly_stats.py  # Monthly team/player rankings
│   ├── location_stats.py # Home/away splits analysis
│   ├── personal_ranks.py # Extended stats categories
│   └── injuries.py       # Injury report tracking
├── tests/                # Test scripts and exploration
├── docs/                 # API documentation (YAML specs)
└── main.py              # Primary entry point
```

## Usage

**Main scheduler (production):**
```bash
python main.py
```

**Personal analytics:**
```bash
python run_monthly_stats.py    # Current month rankings
python run_location_stats.py   # Home/away splits
```

## Configuration

Required environment variables (`.env`):
- API authentication tokens
- Webhook URLs
- Base URLs for data sources

See [config.py](src/config.py) for all required variables.

## Key Modules

- **formatter.py**: Main logic for assembling game previews with relevant stats
- **rankings.py**: Fetches and caches team/player rankings to minimize API calls
- **personal_ranks.py**: Extended stats for deeper analytics (monthly, location-based)
- **slack_client.py**: Handles message formatting and posting

## Development

To modify what stats are shown, edit the stat categories in [rankings.py](src/rankings.py) or [personal_ranks.py](personal/personal_ranks.py).

To change message formatting, edit [formatter.py](src/formatter.py) (production) or `personal/*_stats.py` (analytics).