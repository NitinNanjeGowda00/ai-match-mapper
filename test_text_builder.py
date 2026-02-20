from app.inference.text_builder import build_match_text

match = {
    "sport": "football",
    "league": "Premier League Women",
    "home_team": "Arsenal W",
    "away_team": "Chelsea W",
    "kickoff_utc": "2026-02-15T18:30:00Z"
}

print(build_match_text(match))
