# scripts/run_production_full_output.py

import requests
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timezone

from app.inference.pipeline import run_inference

# -----------------------------
# CONFIG
# -----------------------------

BET365_URL = "https://sports-bet-api.allinsports.online/api/matches/get-bet365-matches-with-odds/"
ODDSPORTAL_URL = "https://sports-bet-api.allinsports.online/api/matches/get-odds-portal-matches-with-odds/"

OUT_FILE = Path("data/production_full_output.json")

REQUEST_TIMEOUT = 30


# -----------------------------
# UTIL
# -----------------------------

def unix_to_iso(ts: int):
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")


# -----------------------------
# FETCH WITH PAGINATION
# -----------------------------

def fetch_all_pages(base_url: str) -> List[Dict]:

    all_rows = []
    page = 1

    while True:

        url = f"{base_url}?page={page}"

        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        data = response.json()

        if not data.get("status"):
            break

        rows = data.get("data", {}).get("rows", [])

        if not rows:
            break

        all_rows.extend(rows)

        total_pages = data.get("data", {}).get("totalPages", 1)

        print(f"Fetched page {page}/{total_pages}")

        if page >= total_pages:
            break

        page += 1

    return all_rows


# -----------------------------
# NORMALIZATION
# -----------------------------

def normalize_match(raw: Dict) -> Dict:

    return {
        "id": raw.get("id"),
        "sport": (raw.get("sport") or "").lower(),
        "league": raw.get("league", {}).get("league_name_en"),
        "home_team": raw.get("home_team"),
        "away_team": raw.get("away_team"),
        "kickoff_utc": unix_to_iso(raw.get("commence_time")),
        "categories": [],  # optional for now
    }


# -----------------------------
# MAIN
# -----------------------------

def main():

    print("Fetching Bet365 matches...")
    bet365_raw = fetch_all_pages(BET365_URL)

    print("Fetching OddsPortal matches...")
    op_raw = fetch_all_pages(ODDSPORTAL_URL)

    print(f"Total Bet365 matches: {len(bet365_raw)}")
    print(f"Total OddsPortal matches: {len(op_raw)}")

    # Only unmapped
    op_unmapped = [m for m in op_raw if not m.get("isMapped")]

    print(f"Unmapped OddsPortal matches: {len(op_unmapped)}")

    bet365_matches = [normalize_match(m) for m in bet365_raw]
    results = []

    for raw_op in op_unmapped:

        op_match = normalize_match(raw_op)

        result = run_inference(
            op_match=op_match,
            b365_matches=bet365_matches,
        )

        candidates = result.get("candidates", [])

        if not candidates:
            continue

        best = candidates[0]

        output_row = {
            "platform": "ODDSPORTAL",
            "bet365_match": best.get("id"),
            "provider_id": op_match.get("id"),
            "confidence": round(best.get("confidence", 0.0), 4),
            "is_checked": False,
            "is_mapped": result.get("decision") == "AUTO_MATCH",
            "reason": result.get("reason"),
            "switch": best.get("swapped", False),
        }

        results.append(output_row)

    print(f"Generated {len(results)} mappings")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("✅ Production Full Output Generated")
    print(f"Saved to: {OUT_FILE}")


if __name__ == "__main__":
    main()
