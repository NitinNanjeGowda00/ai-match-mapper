# app/inference/adapters.py

from app.inference.time_utils import unix_to_iso


def adapt_bet365_match(raw: dict) -> dict:
    return {
        "id": raw.get("id"),
        "sport": raw.get("sport", "").lower(),
        "league": raw.get("league", {}).get("name", ""),
        "home_team": raw.get("home_team"),
        "away_team": raw.get("away_team"),
        "kickoff_utc": unix_to_iso(raw["commence_time"]),
    }


def adapt_oddsportal_match(raw: dict) -> dict:
    return {
        "id": raw.get("id"),
        "sport": raw.get("sport", "").lower(),
        "league": raw.get("league", {}).get("league_name_en", ""),
        "home_team": raw.get("home_team"),
        "away_team": raw.get("away_team"),
        "kickoff_utc": unix_to_iso(raw["commence_time"]),
    }
