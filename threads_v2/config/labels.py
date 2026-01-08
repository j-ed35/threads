"""
Centralized text labels and section headers for threads_v2.

All static text used in Slack messages is defined here for easy maintenance.
"""

# Section headers used in messages
SECTION_HEADERS = {
    "notables": "NOTABLES",
    "milestones": "MILESTONES",
    "gtd": "GTD/QUESTIONABLE",
    "injuries": "INJURIES",
    "streaks": "STREAKS",
    "rankings": "TOP 10 RANKINGS",
}

# Text labels for formatting
LABELS = {
    "no_games": "No NBA games scheduled for today",
    "game_header": "NBA Games",
    "at": "at",
    "vs": "vs",
    "l10": "L10",
    "home": "Home",
    "away": "Away",
    "streak": "Streak",
    "ranks": "ranks",
    "in": "in",
}

# Stat display names
STAT_NAMES = {
    # Team stats - Basic
    "BASE_PTS": "PPG",
    "BASE_FG_PCT": "FG%",
    "BASE_FG3_PCT": "3P%",
    "BASE_AST": "AST",
    "BASE_REB": "REB",
    "BASE_STL": "STL",
    "BASE_BLK": "BLK",
    "OPP_PTS": "Opp PPG",
    # Team stats - Advanced
    "ADV_TM_NET_RATING": "Net RTG",
    "ADV_TM_OFF_RATING": "Off RTG",
    "ADV_TM_DEF_RATING": "Def RTG",
    # Team stats - Misc
    "MISC_PTS_OFF_TOV": "PTS Off TOV",
    "MISC_PTS_2ND_CHANCE": "PTS 2nd Chance",
    "MISC_PTS_FB": "PTS Fast Break",
    "MISC_PTS_PAINT": "PTS Paint",
    # Player stats
    "PTS": "PPG",
    "AST": "APG",
    "REB": "RPG",
    "STL": "SPG",
    "BLK": "BPG",
    "FG_PCT": "FG%",
    "FG3M": "3PM",
    "FG3_PCT": "3P%",
    "BASE_DD2": "Double Doubles",
    "BASE_TD3": "Triple Doubles",
}

# Month abbreviations for standings
MONTHS = ["oct", "nov", "dec", "jan", "feb", "mar", "apr", "may", "jun"]
