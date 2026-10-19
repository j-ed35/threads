from .mapping import PLAYERS_EXCLUDED

GTD_STATUSES = {"GTD", "QUESTIONABLE", "DOUBTFUL"}


def index_injuries(data: dict) -> dict:
    """Group the league injury report by teamId: {team_id: {"GTD": [player], "OUT": [player]}}."""
    index = {}
    for player in data.get("players", []):
        if player.get("playerName", "") in PLAYERS_EXCLUDED:
            continue
        status = player.get("injuryStatus", "").upper()
        bucket = "GTD" if status in GTD_STATUSES else "OUT" if status == "OUT" else None
        if bucket:
            team = index.setdefault(player.get("teamId"), {"GTD": [], "OUT": []})
            team[bucket].append(player)
    return index


def format_summary(injuries: dict, away_id, home_id) -> str:
    """Parent-message lines: `:gtd: away names | home names` and the same for `:out:`."""
    empty = {"GTD": [], "OUT": []}
    away, home = injuries.get(away_id, empty), injuries.get(home_id, empty)
    lines = []
    for bucket, emoji in (("GTD", ":gtd:"), ("OUT", ":out:")):
        parts = [
            ", ".join(p["playerName"] for p in team[bucket])
            for team in (away, home)
            if team[bucket]
        ]
        if parts:
            lines.append(f"{emoji} {' | '.join(parts)}")
    return "\n".join(lines)


def format_thread(injuries: dict, away_id, home_id, away_tri: str, home_tri: str) -> str:
    """Detailed injury reply listing each player's injury and status, away team first."""
    empty = {"GTD": [], "OUT": []}
    teams = ((away_tri, injuries.get(away_id, empty)), (home_tri, injuries.get(home_id, empty)))
    sections = []
    for bucket, title in (("GTD", ":gtd: *GTD/QUESTIONABLE*"), ("OUT", ":out: *OUT*")):
        rows = [
            f":_{tri.lower()}: {p['playerName']} - {p.get('injuryType', '')} ({p.get('injuryStatus', '')})"
            for tri, team in teams
            for p in team[bucket]
        ]
        if rows:
            sections.append("\n".join([title, *rows]))
    if not sections:
        return ""
    # Hardcoded from v1, which ran from the 12:15pm ET GitHub Action.
    return "_Injuries Current as of 12PM ET_\n\n" + "\n\n".join(sections)
