# Threads

## Overview

Automated NBA game information system that posts daily game schedules to Slack with enhanced statistical context and threaded discussions for each game.

## Features

### Game Information
- Daily NBA game schedules with matchup details
- Game times displayed in Eastern Time
- Team records (W-L) for both teams
- National broadcast information with network indicators

### Team Statistics
- Current win/loss streak for each team
- Last 10 games record (L10)
- Top 10 team rankings across multiple statistical categories:
  - Points Per Game (PPG)
  - Field Goal Percentage (FG%)
  - Three-Point Percentage (3P%)
  - Assists (AST)
  - Rebounds (REB)

### Player Statistics
Top 10 league rankings displayed when players from featured teams appear:
- Points Per Game (PPG)
- Assists Per Game (APG)
- Rebounds Per Game (RPG)
- Steals Per Game (SPG)
- Blocks Per Game (BPG)
- Field Goal Percentage (FG%)
- Three-Pointers Made (3PM)
- Three-Point Percentage (3P%)

### Automation
- Automated GitHub Actions workflow runs daily
- Configurable schedule via cron expression
- Individual Slack threads created for each game

## How the Formatter Works

The [formatter.py](src/formatter.py) module processes game data through several stages:

1. **Data Aggregation**: Fetches game schedules, team standings, and league-wide rankings
2. **Rankings Processing**: Pre-loads all top-10 rankings for teams and players to minimize API calls
3. **Game Formatting**: For each game, assembles:
   - Matchup header with records and game time
   - Team performance metrics (streak, L10)
   - Relevant team rankings (only if team ranks in top 10 for a stat)
   - Relevant player rankings (only if a player from the team ranks in top 10)
4. **Output Generation**: Produces formatted text optimized for Slack's markdown rendering

The formatter uses a lookup-based approach to efficiently match team IDs and tricodes against pre-fetched rankings data, ensuring fast performance even with multiple games per day.

## Development

### Updating Game Format
Edit [src/formatter.py](src/formatter.py) to change how games are displayed. Key methods:
- `format_games()` - Main entry point for formatting all games
- `_format_single_game()` - Individual game formatting logic
- `_format_team_rankings()` - Team statistics display
- `_format_player_rankings()` - Player statistics display

### Changing Slack Message Format
Edit [src/slack_client.py](src/slack_client.py) in the `send_games()` method.

### Configuration
Update [.github/workflows/daily_schedule.yml](.github/workflows/daily_schedule.yml) for scheduling:
```yaml
on:
  schedule:
    - cron: '0 15 * * *'   # 11:00 AM EDT
```

## Project Structure
```
threads/
├── .github/workflows/      # GitHub Actions automation
├── src/                    # Source code
│   ├── config.py          # Configuration management
│   ├── nba_api.py         # NBA API client
│   ├── rankings.py        # Rankings data fetcher and processor
│   ├── formatter.py       # Game and statistics formatting
│   ├── broadcaster_mapping.py  # Network emoji mappings
│   └── slack_client.py    # Slack integration
├── main.py                # Production entry point
└── test_slack.py          # Test script with mock data
```

## Technical Notes

- All statistics are fetched and cached at runtime to minimize API calls
- Rankings data is pre-loaded once per execution for efficiency
- Team and player rankings are filtered to only show top-10 appearances
- Time zone handling converts UTC game times to Eastern Time
- The system is designed for read-only operations on publicly available game data