# threads — NBA daily game threads for Slack

Posts one Slack message per NBA game, with a threaded reply for secondary rankings, home/away records and, on some channels, injury details. Regular season only; no playoff features. A GitHub Action posts to #daily-threads every day; #Mookie-Blaylock and #ed-testing are run by hand.

## Flow of `main.py`

1. Choose a channel from the flags. `Config.channel()` validates the API keys and that channel's ID only, then returns `(channel_id, ChannelSettings)`.
2. Work out the date (`--date M-D-YY` or today) and the season from it (`season_for`).
3. Load in parallel: the full-season schedule, standings, the injury report (only if `include_injuries`), and every team and player top-10 ranking (`RankingsChecker.load`, also parallel). If standings fail, the run continues without seeds, streaks or home/away lines. A single failed ranking, leaderboard or roster fetch is logged and skipped.
4. Filter the schedule to the date's regular-season games: `gameId` starting `002`, which includes NBA Cup group and knockout games. Preseason (`001`), All-Star (`003`), playoffs (`004`), play-in (`005`) and the Cup final (`006`) are skipped. If no games remain, post "No NBA games scheduled for …" and stop.
5. If `include_milestones`: load all career leaderboards and each playing team's roster once, in parallel (`MilestonesChecker.load`).
6. Format every game (`GameFormatter.format_game`), then post `:nba: N Games for M-D-YY` plus two `———` dividers, then each game's parent and replies.

## Module map

| File | Purpose |
|---|---|
| `main.py` | CLI and run orchestration |
| `leaders.py` | Posts all-time career leaders for one stat to #Mookie-Blaylock, or writes a CSV |
| `src/config.py` | Env vars, `CHANNELS` table, `ChannelSettings`, `season_for`, `Config.validate` |
| `src/nba_api.py` | `NBAClient`: every api.nba.com request goes through `_get`, which counts calls |
| `src/rankings.py` | `RankingsChecker`: team stats (querytool) and player leaders, indexed by teamId and tricode |
| `src/formatter.py` | `GameFormatter`: builds the parent message, rankings reply and injury reply |
| `src/injuries.py` | Indexes the league injury report by team; formats the summary and the detail reply |
| `src/milestones.py` | `MilestonesChecker`: all-time career milestone lines |
| `src/mapping.py` | Broadcaster → Slack emoji map; `PLAYERS_EXCLUDED` from injury output |
| `src/slack_client.py` | `chat.postMessage` with thread replies |

## Message format

Parent message (every channel):
```
#3 LAL (45-25) :_lal: at :_orl: #6 ORL (38-31) | 7:00 PM ET | :_ESPN:
:_lal: W 8 | L10: 9-1
:_orl: L 3 | L10: 7-3
:t10: LAL ranks #1 in FG% (50.0), #3 in PPG (118.2), #7 in Opp PPG (108.9)
:t10: Luka Dončić (LAL) ranks #1 in PPG (33.4), #3 in APG (8.4), #1 in 3PM (4.0)
:t10: Other Top 10s threaded
:notable: NOTABLES
:mst: MILESTONES
:out: INJURIES
```
Reply 1 (always posted): `:_lal: Away: W-L | L10: …`, `:_orl: Home: W-L | L10: …`, then the thread rankings. There is no `@` title line.

Mookie keeps the same layout and only adds information:
- `:mst: MILESTONES` is replaced by the game's milestone lines (`:mst: Brook Lopez (1,945) needs 6 BLK …`).
- `:out: INJURIES` is replaced by the injury summary (`:gtd: away names | home names`, `:out: …`).
- Reply 2: the `:gtd: *GTD/QUESTIONABLE*` / `:out: *OUT*` detail lists.

If a Mookie game has no milestones or no injuries, the placeholder line stays.

Rules:
- Header: the away side reads `#seed TRI (W-L) :_tri:`, the home side reads `:_tri: #seed TRI (W-L)`, so the logos sit on either side of "at". The seed is standings `playoffRank`, the W-L record comes from the schedule, and the clinch indicator follows the record (`format_clinch_indicator`). All national TV broadcasters (`broadcasterScope == "natl"` and `broadcasterMedia == "tv"`) are mapped through `BROADCASTER_EMOJI_MAP`, deduplicated by emoji, and joined with spaces.
- Standings lines show even at 0-0 (start of season). This is intentional.
- Team rankings: one line per team per message, ranks 1–10 ordered by rank. Parent stats are `PPG, FG%, 3P%, BLK, Opp PPG, 3PM`; thread stats are `Net RTG, Off RTG, Def RTG, AST, REB, STL`.
- Player rankings: one line per player, players alphabetical within a team, stats in the order PPG, RPG, APG, FG%, 3P%, 3PM, SPG, BPG. Split by rank: ranks 1–5 go in the parent, 6–10 in the thread, so a player can appear in both. FG%/3P% arrive as fractions and are shown ×100 to 1 decimal.
- `:t10: Other Top 10s threaded` appears only if the thread has at least one ranking line.
- Early season: the player leaders endpoint returns the previous season when the requested one has no games yet. `get_top_players` drops any response whose `season` doesn't match, so player and team ranks stay empty until games are played.
- Emojis: team logos `:_{tricode_lower}:`, `:t10:`, `:notable:`, `:mst:`, `:gtd:`, `:out:`, run header `:nba:`.

## Channels

| Flag | Channel | Env var | Injuries | Milestones |
|---|---|---|---|---|
| *(none)* | #ed-testing | `SLACK_CHANNEL_ID_ED_TESTING` | off | off |
| `--daily_threads` | #daily-threads | `SLACK_CHANNEL_ID_NBA_DAILY_THREADS` | off | off |
| `--mookie` | #Mookie-Blaylock | `SLACK_CHANNEL_ID_MOOKIE_BLAYLOCK` | on | on |

Shell shortcuts (`nba` function in `~/.zshrc`; a trailing `M-D-YY` becomes `--date`):

| Command | Runs |
|---|---|
| `nba threads [date]` | `main.py --daily_threads` |
| `nba threads ed [date]` | `main.py` (#ed-testing) |
| `nba mookie [date]` | `main.py --mookie` |
| `nba mookie <stat> [csv]` | `leaders.py <stat> [--csv]` |

**#ed-testing mirrors #daily-threads exactly.** In `src/config.py` both entries point at the same `DAILY_THREADS` settings object and run the same code path; only the channel ID differs. Never give #ed-testing its own settings, and never branch on the channel name anywhere else. A per-channel behavior belongs in `ChannelSettings`.

## Environment variables

See `.env.example`.

| Var | Used by |
|---|---|
| `NBA_API_KEY` | schedule |
| `NBA_STANDINGS_KEY` | standings |
| `QUERY_TOOL_API_KEY` | team rankings, career leaderboards (milestones, `leaders.py`) |
| `STATS_API_KEY` | player leaders, injuries, rosters |
| `NBA_ALERTS_API_KEY` | not used by any request; kept for reference |
| `SLACK_BOT_TOKEN` | Slack |
| `SLACK_CHANNEL_ID_*` | one per channel (above) |
| `ALL_TIME_LISTS_DIR` | optional; output dir for `leaders.py --csv` |

## Deployment

- `.github/workflows/daily_schedule.yml` ("Daily NBA Schedule") runs `uv run python main.py --daily_threads` on cron `15 16 * * *`, which is 12:15 PM ET during daylight saving and 11:15 AM ET in winter. It can also be run by hand from the Actions tab.
- The workflow passes only the vars a `--daily_threads` run needs. Its repo secrets are `NBA_API_KEY`, `NBA_STANDINGS_KEY`, `QUERY_TOOL_API_KEY`, `STATS_API_KEY`, `SLACK_BOT_TOKEN` and `SLACK_CHANNEL_ID_NBA_DAILY_THREADS`.
- Scheduled workflows run only from the default branch (`main`). Turn the workflow off in the offseason with `gh workflow disable "Daily NBA Schedule"`, and back on with `gh workflow enable`.
- The Slack bot token can post but cannot read history (no `channels:history` scope). If a real run fails partway, check the channel by hand before re-running, or the posted games will be duplicated.

## Running

```bash
uv sync
uv run python main.py                    # #ed-testing
uv run python main.py --daily_threads    # #daily-threads
uv run python main.py --mookie           # #Mookie-Blaylock
uv run python main.py --date 3-21-26     # a specific date (combine with any channel flag)
uv run python leaders.py AST             # all-time top 20 assists -> #Mookie-Blaylock
uv run python leaders.py TD3 -n 5        # custom count (defaults: 20, DD2 15, TD3 10)
uv run python leaders.py PTS --csv       # $ALL_TIME_LISTS_DIR/nba_points_leaders.csv
```
`leaders.py` stat tags: GP, PTS, REB, AST, STL, BLK, 3PM/FG3M, FGM, FTM, OREB, DREB, TOV, MIN, FG3A, DD2, TD3 (a leading `-` is accepted). DD2/TD3 come from `/querytool/season/player` with `SeasonYear=All` because the career endpoint lacks them.

## Dry run (no Slack)

Test format changes with a dry run first, then a real post to #ed-testing. Don't post to #daily-threads or #Mookie-Blaylock unless Jacob asks. Patch `SlackClient.send_message` to print instead of post:

```bash
uv run python - --mookie --date 3-21-26 <<'EOF'
import sys
from src.slack_client import SlackClient
SlackClient.send_message = lambda self, text, thread_ts=None: (print(("  ↳ " if thread_ts else "") + text, end="\n\n"), {"ts": "1"})[1]
sys.argv[0] = "main.py"
import runpy; runpy.run_path("main.py", run_name="__main__")
EOF
```
`send_game_with_thread` calls `send_message`, so replies print too (prefixed `↳`). Real posts wait out Slack 429 rate limits (`Retry-After`); a full slate is roughly 3 messages per game. The same patch works for `leaders.py`. A real channel ID env var must still be set, because config validation runs first; nothing is posted.

## Adding a stat

- **Team ranking**: add `measure: (response key, label, lower_is_better)` to `RankingsChecker.TEAM_STATS`, then put the label in `GameFormatter.PARENT_TEAM_STATS` or `THREAD_TEAM_STATS`. The response key doubles as the sort column.
- **Player ranking**: add `statCategory: (response key, label)` to `RankingsChecker.PLAYER_STATS`. Its position in the dict sets the display order. Add the label to `GameFormatter.PERCENT_STATS` if the API returns a fraction.
- **Milestone**: add `measure: (label, sort column, threshold)` to `MilestonesChecker.STATS`.
- **leaders.py**: add a tag to `STATS`; add it to `SEASON_ENDPOINT_STATS` if the career endpoint doesn't return it.

## Tuning milestones

`MilestonesChecker.STATS` thresholds (PTS 50, REB/AST/FGM 15, FTM/STL/BLK/3PM 10) are carried over from the WNBA bot, so treat them as a starting point and tune them for NBA volumes. `MAX_RANK = 20` reports only passes into the all-time top 20, so a player is checked only from rank 21 up. `needed = above − player + 1`, because matching only ties. Active players are matched by `playerId` against that day's team rosters, not by team abbreviation, because the career endpoint reports multi-team players as "MTM"/teamId 0.

## Season rollover

Nothing to change. `season_for(date)` returns `YYYY-YY` from the target date (October or later starts a new season), and every request uses it. `--date` on a past date uses that date's season.
