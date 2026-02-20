def build_text(match: dict) -> str:
    return f"""
    {match.get("sport","")}
    {match.get("league","")}
    {match.get("home_team","")} vs {match.get("away_team","")}
    """